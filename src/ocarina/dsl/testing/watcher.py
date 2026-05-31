"""Concurrent observer for test scenarios.

A Watcher runs in a background daemon thread alongside a test chain.
It polls a user-defined callback at a fixed interval, giving the callback
full control over what to detect, how to deduplicate, and when to report.

Lifecycle (managed by TestSuite):
    1. start(driver, logger, take_screenshot)
           → spawns a daemon thread that calls callback(self) in a loop.
    2. [test_chain executes in the main thread]
    3. stop()
           → signals the loop to exit and joins the thread.

The callback receives the Watcher instance itself, which exposes:
    - watcher.driver          — the live WebDriver (read-only property)
    - watcher.cache           — a mutable set[str] for DOM fingerprints
    - watcher.report(msg)     — logs + screenshots when something is detected

Deduplication pattern:
    The callback is responsible for avoiding repeated reports of the same
    element. The recommended approach is to compute a fingerprint (text,
    hash, element id, etc.) and check it against watcher.cache before
    calling watcher.report(). Once stored in cache, the fingerprint will
    never be reported again for the lifetime of the watcher.

Error isolation:
    Any exception raised inside the callback is silently suppressed.
    The watcher thread will never crash the test, never propagate errors,
    and never interfere with the main test chain execution.

Example:
    >>> def watch_cookie_banner(watcher: Watcher) -> None:
    ...     banner = CookieBanner(watcher.driver)
    ...     if not banner.is_visible():
    ...         return
    ...     fingerprint = banner.get_text()
    ...     if fingerprint in watcher.cache:
    ...         return
    ...     watcher.cache.add(fingerprint)
    ...     watcher.report(f"Cookie banner detected: {fingerprint!r}")
    ...
    >>> scenario = Scenario(
    ...     test_chain=[...],
    ...     watchers=[
    ...         Watcher(callback=watch_cookie_banner, poll_interval=1.0),
    ...     ],
    ... )

"""

import threading
from contextlib import suppress
from typing import TYPE_CHECKING, final

if TYPE_CHECKING:
    from collections.abc import Callable

    from ocarina.ports.ilogger import ILogger
    from ocarina.ports.itake_screenshot import ITakeScreenshot


@final
class Watcher[Driver]:
    """Concurrent observer that enriches test reports with live page signals.

    Runs as a daemon thread alongside the test chain, polling a user-defined
    callback at a fixed interval. The callback decides what to detect, how
    to deduplicate, and when to emit a log + screenshot via report().

    Args:
        callback:      A function receiving this Watcher instance.
                       Called repeatedly at every poll cycle.
                       Must never raise — exceptions are suppressed internally.
                       Use watcher.driver to access the WebDriver,
                       watcher.cache to deduplicate,
                       and watcher.report() to emit a signal.
        name:          Name of the watcher.
        poll_interval: Seconds to wait between callback invocations.
                       Defaults to 0.5s. Lower values increase sensitivity
                       but add CPU pressure. 0.5 to 1.0s is appropriate for
                       most browser observation use cases.

    """

    def __init__(
        self,
        *,
        callback: Callable[[Watcher[Driver]], None],
        name: str,
        poll_interval: float | None = None,
    ) -> None:
        """Initialize the watcher with its callback and polling interval."""
        self._callback = callback
        self._poll_interval = (
            poll_interval if poll_interval is not None and poll_interval > 0.1 else 0.5  # noqa: PLR2004
        )
        # Per-call: a fresh Event is created on every start() and passed by
        # argument to the worker thread. The previous Event (if any) is set
        # here so that a leaked thread from a stop() that timed out can never
        # see a "cleared" event and resume polling against new state.
        self._stop_event: threading.Event | None = None
        self._cache: set[str] = set()
        self._thread: threading.Thread | None = None
        self._logger: ILogger | None = None
        self._take_screenshot: ITakeScreenshot[Driver] | None = None
        self._driver: Driver | None = None
        self.name = name

    @property
    def driver(self) -> Driver:
        """The live WebDriver instance for this test attempt.

        Injected by TestSuite at start() time.
        Available inside the callback for the full duration of the test.

        Raises:
            RuntimeError: If accessed before start() has been called.

        Returns:
            The WebDriver instance passed to start().

        """
        if self._driver is None:
            msg = "Watcher.driver accessed before start() was called."
            raise RuntimeError(msg)
        return self._driver

    @property
    def cache(self) -> set[str]:
        """Mutable set of DOM fingerprints already reported.

        Owned by the callback — the Watcher never reads or modifies it.
        Use it to deduplicate signals across poll cycles.

        Typical usage:
            fingerprint = element.text or hash(element.id)
            if fingerprint in watcher.cache:
                return
            watcher.cache.add(fingerprint)
            watcher.report(f"Detected: {fingerprint}")

        Returns:
            A mutable set[str] scoped to this Watcher instance.

        """
        return self._cache

    def report(self, message: str, *, label: str = "WATCHER") -> None:
        """Emit a log entry and capture a screenshot.

        Call this from inside the callback when something worth reporting
        is detected. Both the log and the screenshot are silently suppressed
        on failure — a broken report must never crash the watcher thread.

        Args:
            message: Human-readable description of what was detected.
                     Will appear in the logger output and the Allure report.
            label:   Screenshot filename label. Defaults to "WATCHER".
                     Use a descriptive label to distinguish screenshots
                     from multiple watchers in the same scenario.

        Example:
            >>> watcher.report("Unexpected modal appeared", label="MODAL")

        """
        if (
            self._driver is None
            or self._logger is None
            or self._take_screenshot is None
        ):
            return

        # Encode the invariant: we report only while actively observing. Once
        # stop() has been requested, a callback still in flight from before the
        # stop must not log or screenshot. This also closes a benign race at
        # teardown where the driver gets disposed just as a leaked callback
        # would have tried to screenshot it.
        if self._stop_event is None or self._stop_event.is_set():
            return

        with suppress(Exception):
            self._logger.info(message)
            self._take_screenshot(self._driver, self._logger, label)

    def start(
        self,
        driver: Driver,
        logger: ILogger,
        take_screenshot: ITakeScreenshot[Driver],
    ) -> None:
        """Start the observation loop in a background daemon thread.

        Called by TestSuite before test_chain executes.
        Injects the runtime dependencies (driver, logger, screenshot)
        that the callback needs, then spawns the polling thread.

        The thread is a daemon — it will not prevent process exit if
        TestSuite forgets to call stop().

        Args:
            driver:          The live WebDriver for this test attempt.
            logger:          The ILogger scoped to the current test taxonomy.
            take_screenshot: The ITakeScreenshot callable bound to the driver.

        """
        # Defensively terminate any thread leaked from a previous start()
        # whose stop()/join() timed out. Its loop holds the previous Event
        # in its local frame; setting it here guarantees the leaked thread
        # exits at the end of its current callback iteration instead of
        # racing with the new thread on shared self._driver / self._logger.
        if self._stop_event is not None:
            self._stop_event.set()

        self._driver = driver
        self._logger = logger
        self._take_screenshot = take_screenshot
        stop_event = threading.Event()
        self._stop_event = stop_event
        self._thread = threading.Thread(
            target=self._loop, args=(stop_event,), daemon=True
        )
        self._thread.start()

    def stop(self) -> None:
        """Signal the observation loop to stop and wait for the thread to exit.

        Called by TestSuite after test_chain completes, regardless of whether
        the test passed or failed.
        to finish its current cycle and exit cleanly.

        Does not raise even if the thread is slow or unresponsive — the
        daemon flag ensures it is collected by the process regardless.

        """
        if self._stop_event is not None:
            self._stop_event.set()
        if self._thread is not None:
            self._thread.join(timeout=self._poll_interval * 2)

    def _loop(self, stop_event: threading.Event) -> None:
        """Poll loop executed in the background thread.

        Repeatedly calls callback(self) at poll_interval, suppressing any
        exception that escapes the callback. Exits cleanly when stop_event
        is set by stop().

        Never raises. Never blocks the main thread.

        ``stop_event`` is bound to *this* thread's lifetime. A subsequent
        start() will set this Event before swapping in a fresh one for the
        new thread — see ``start()`` for the rationale.

        """
        while not stop_event.is_set():
            with suppress(Exception):
                self._callback(self)
            stop_event.wait(self._poll_interval)
