"""Playwright driver actor — confines all Playwright calls to one owner thread.

Playwright's *sync* API binds every object it hands out (Playwright, Browser,
BrowserContext, Page, Locator, ...) to the thread that called
``sync_playwright().start()``. Touching any of them from another thread raises
``greenlet.error: cannot switch to a different thread``.

That collides head-on with Ocarina's threaded model:

- ``WebDriversPool.warmup()`` pre-creates drivers in a dedicated warmup thread
  and hands them to *worker* threads via a queue.
- ``Watcher`` polls alongside the test chain in its own daemon thread.

``PlaywrightDriver`` resolves this by owning a single-thread executor: the
Playwright objects live on that one owner thread, and every interaction is
marshalled onto it via :meth:`submit`. The handle itself is therefore safe to
create in one thread and use from another — only the *work* ever touches
Playwright, and that work always runs on the owner thread. This preserves
Ocarina's pool, warmup, and parallelism without giving up the sync API.

The driver exposes ``quit()`` and ``save_screenshot()`` so it slots into the
existing generic infrastructure (:class:`~ocarina.infra.driver_builder.DriverBuilder`
disposal and the :class:`~ocarina.infra.screenshotter.ScreenshotDriver` protocol)
unchanged.
"""

import threading
import uuid
from concurrent.futures import Future
from concurrent.futures import TimeoutError as FuturesTimeoutError
from contextlib import suppress
from pathlib import Path
from queue import Queue
from typing import TYPE_CHECKING, Any, final

from playwright.sync_api import sync_playwright

from ocarina.custom_errors.test_framework.driver_died import DriverDiedError

if TYPE_CHECKING:
    from collections.abc import Callable

    from playwright.sync_api import Browser, BrowserContext, Page, Playwright

    from ocarina.custom_types.playwright.supported_browsers import (
        SupportedPlaywrightBrowser,
    )

_TRACE_ID_LENGTH = 8
_MAX_TRACE_NAME_RETRIES = 500

# Extra wait, in seconds, added on top of the page's ``wait_timeout`` to form the
# per-call marshalling budget. The budget MUST exceed ``wait_timeout`` so that a
# legitimate Playwright auto-wait (which can run for the full ``wait_timeout``)
# is never mistaken for a dead transport. The margin only needs to cover the
# marshalling overhead plus a little slack for back-to-back waits inside one call.
_DEFAULT_CALL_TIMEOUT_MARGIN_S = 30.0


def _generate_unique_trace_path(trace_dir: str) -> str:
    """Pick a free ``trace_<id>.zip`` in ``trace_dir``, retrying on collision.

    Mirrors the screenshotter's filename strategy: a short random id kept
    collision-free by checking the disk and retrying (up to 500 times), rather
    than by a long name. Files accumulate — nothing is overwritten or cleaned.

    Raises:
        RuntimeError: If no free name is found after the retry budget (which,
            with random ids, means the directory is effectively saturated).

    """
    directory = Path(trace_dir)
    directory.mkdir(parents=True, exist_ok=True)
    for _ in range(_MAX_TRACE_NAME_RETRIES):
        candidate = directory / f"trace_{uuid.uuid4().hex[:_TRACE_ID_LENGTH]}.zip"
        if not candidate.exists():
            return str(candidate)
    msg = (
        f"Could not generate a unique trace filename in {trace_dir} "
        f"after {_MAX_TRACE_NAME_RETRIES} attempts."
    )
    raise RuntimeError(msg)


@final
class _OwnerThread:
    """A single owner thread that runs submitted callables in submission order.

    Behaves like ``ThreadPoolExecutor(max_workers=1)`` but with one crucial
    difference: the worker is a **daemon** thread. ``ThreadPoolExecutor`` workers
    are non-daemon and are joined by an ``atexit`` hook on interpreter shutdown;
    a worker wedged on a dead Playwright transport pipe would never return, so
    that join — and therefore process exit — would hang forever.

    A daemon worker is abandoned at exit instead of joined, so a wedged owner
    thread can never block the process from terminating. We also never ``join``
    it ourselves (see :meth:`stop`): a future already running on the worker is
    not cancellable, so the only safe move for a dead driver is to walk away.
    """

    def __init__(self, name: str) -> None:
        """Spawn the daemon worker thread."""
        self._queue: Queue[tuple[Callable[[], Any], Future[Any]] | None] = Queue()
        self._thread = threading.Thread(target=self._run, name=name, daemon=True)
        self._thread.start()

    def submit[T](self, fn: Callable[[], T]) -> Future[T]:
        """Queue ``fn`` for the owner thread and return its pending future."""
        future: Future[T] = Future()
        self._queue.put((fn, future))
        return future

    def _run(self) -> None:
        """Drain the queue on the owner thread until asked to stop."""
        while True:
            item = self._queue.get()
            if item is None:
                return
            fn, future = item
            if not future.set_running_or_notify_cancel():
                continue
            try:
                result = fn()
            except BaseException as exc:  # noqa: BLE001 — marshal any failure back.
                future.set_exception(exc)
            else:
                future.set_result(result)

    def stop(self) -> None:
        """Ask the worker to exit after its current task. Never joins.

        If the worker is wedged on a dead transport it will never see the
        sentinel — that is fine: it is a daemon thread and will be reaped at
        interpreter exit without blocking it. The accepted cost is a per-death
        leak: the abandoned thread, the stuck call, and its closure stay
        referenced for the process lifetime. Under repeated deaths these
        accumulate — a deliberate trade against hanging the whole run.
        """
        self._queue.put(None)


@final
class PlaywrightDriver:
    """A Playwright session whose every call runs on a private owner thread."""

    def __init__(  # noqa: PLR0913
        self,
        *,
        browser: SupportedPlaywrightBrowser,
        headless: bool,
        wait_timeout: int,
        user_data_dir: str,
        record_video_dir: str | None = None,
        trace_dir: str | None = None,
        call_timeout_margin: float = _DEFAULT_CALL_TIMEOUT_MARGIN_S,
    ) -> None:
        """Spawn the owner thread and boot a persistent browser context on it.

        Args:
            browser: One of ``"chromium"``, ``"firefox"``, ``"webkit"``.
            headless: Run without a visible UI.
            wait_timeout: Default auto-wait timeout in seconds. Mapped to
                Playwright's per-page default timeout (the sync-API analogue
                of Selenium's implicit wait). Set once here; for one-off edge
                cases, use Playwright's per-call ``timeout=`` argument at the
                call site.
            call_timeout_margin: Seconds added on top of ``wait_timeout`` to
                form the per-call marshalling budget used by :meth:`submit`. A
                call exceeding ``wait_timeout + call_timeout_margin`` is treated
                as a dead transport (the driver is marked dead and
                ``DriverDiedError`` is raised). Must stay comfortably above the
                marshalling overhead so legitimate auto-waits are never killed.
            user_data_dir: Profile directory for the persistent context
                (supplied by DriverBuilder, cleaned up on dispose).
            record_video_dir: If set, record a video of the session into this
                directory. Must be set at context creation (Playwright cannot
                enable video afterwards); the file is written to disk when the
                driver is disposed, and kept there afterwards.
            trace_dir: If set, capture a Playwright trace (screenshots +
                snapshots) and write ``trace_<id>.zip`` into this directory
                when the driver is disposed — open it with ``playwright
                show-trace``. Files accumulate across runs; nothing is
                overwritten or auto-cleaned.

        """
        self._default_timeout_ms = wait_timeout * 1000
        self._call_timeout_s = wait_timeout + call_timeout_margin
        self._closed = False
        self._dead = False
        self._owner_ident: int | None = None
        self._record_video_dir = record_video_dir
        self._trace_dir = trace_dir
        self._trace_path: str | None = (
            _generate_unique_trace_path(trace_dir) if trace_dir is not None else None
        )
        self._owner = _OwnerThread("ocarina-pw")
        self._playwright: Playwright
        self._context: BrowserContext
        self._browser: Browser | None

        # Boot is bounded by the same budget as a normal call: a node driver can
        # crash *during* startup (launch_persistent_context) just as it can
        # mid-use — and on the on-demand acquire() path nothing else would catch
        # it, so an unbounded boot would wedge the worker with the pool permit
        # held. On timeout we mark the (half-built) driver dead so disposal is a
        # no-op and raise DriverDiedError; the caller releases the permit.
        boot = self._owner.submit(
            lambda: self._boot(
                browser=browser,
                headless=headless,
                user_data_dir=user_data_dir,
            )
        )
        try:
            self._page = boot.result(timeout=self._call_timeout_s)
        except FuturesTimeoutError as exc:
            self._dead = True
            self._closed = True
            self._owner.stop()
            msg = (
                f"Playwright boot exceeded {self._call_timeout_s:g}s; the driver "
                "process likely crashed during startup."
            )
            raise DriverDiedError(msg) from exc

    def _boot(
        self,
        *,
        browser: SupportedPlaywrightBrowser,
        headless: bool,
        user_data_dir: str,
    ) -> Page:
        """Start Playwright and open a persistent context. Runs on owner thread."""
        self._owner_ident = threading.get_ident()
        self._playwright = sync_playwright().start()
        browser_type = getattr(self._playwright, browser)
        # Persistent context (no standalone Browser): mirrors Selenium always
        # routing through a user-data-dir, and lets profiles survive disposal.
        self._browser = None
        context_kwargs: dict[str, Any] = {"headless": headless}
        if self._record_video_dir is not None:
            context_kwargs["record_video_dir"] = self._record_video_dir
        self._context = browser_type.launch_persistent_context(
            user_data_dir, **context_kwargs
        )
        if self._trace_dir is not None:
            self._context.tracing.start(screenshots=True, snapshots=True)
        pages = self._context.pages
        page = pages[0] if pages else self._context.new_page()
        page.set_default_timeout(self._default_timeout_ms)
        page.set_default_navigation_timeout(self._default_timeout_ms)
        return page

    @property
    def is_closed(self) -> bool:
        """Whether :meth:`quit` has been called (driver voluntarily disposed).

        A closed driver is *not* a dead driver — callers (notably the
        healthcheck and the screenshotter) use this to silence benign races at
        teardown without losing the ability to detect a real crash. Note that a
        driver that *died* is also reported as closed (see :attr:`is_dead`).
        """
        return self._closed

    @property
    def is_dead(self) -> bool:
        """Whether the owner transport died (a Playwright call timed out).

        Unlike :attr:`is_closed`, this means a genuine crash: the node driver
        process is gone and the owner thread is wedged on its dead pipe. Such a
        driver must be replaced, not reused.
        """
        return self._dead

    def submit[T](self, fn: Callable[[Page], T]) -> T:
        """Run ``fn(page)`` on the owner thread and return its result.

        The call is bounded by ``wait_timeout + call_timeout_margin``. Exceeding
        it means the owner thread is wedged on a dead Playwright transport (the
        node driver crashed): the driver is marked dead and ``DriverDiedError``
        is raised so the caller can fail/retry with a fresh driver instead of
        hanging forever. The budget is deliberately wider than ``wait_timeout``
        so legitimate auto-waits are never mistaken for a crash.

        ``fn`` must return plain, thread-safe data — never a live Locator or
        ElementHandle, which are owner-thread bound.

        Raises:
            RuntimeError: If called re-entrantly from the owner thread (would
                deadlock), or after :meth:`quit`.
            DriverDiedError: If the driver has died, or this call exceeds the
                marshalling budget (chains the original timeout).

        """
        if threading.get_ident() == self._owner_ident:
            msg = (
                "Re-entrant submit() on the owner thread would deadlock. "
                "You are already on the page thread — call page directly."
            )
            raise RuntimeError(msg)
        if self._dead:
            msg = "PlaywrightDriver is dead (owner transport died)."
            raise DriverDiedError(msg)
        if self._closed:
            msg = "PlaywrightDriver has been disposed."
            raise RuntimeError(msg)
        future = self._owner.submit(lambda: fn(self._page))
        try:
            return future.result(timeout=self._call_timeout_s)
        except FuturesTimeoutError as exc:
            # The future is still running on the (now wedged) owner thread and
            # cannot be cancelled — abandon it. Marking the driver dead/closed
            # makes every later submit() raise and lets quit() short-circuit so
            # disposal never queues behind the stuck call.
            self._dead = True
            self._closed = True
            msg = (
                f"Playwright call exceeded {self._call_timeout_s:g}s; the owner "
                "thread is wedged on a dead driver transport."
            )
            raise DriverDiedError(msg) from exc

    def save_screenshot(self, path: str) -> bool:
        """Capture a viewport screenshot. Satisfies the ScreenshotDriver protocol."""

        def _shot(page: Page) -> bool:
            page.screenshot(path=path)
            return True

        try:
            return self.submit(_shot)
        except Exception:  # noqa: BLE001 — screenshot is best-effort.
            return False

    def quit(self) -> None:
        """Tear down the context/Playwright on the owner thread, then stop it.

        Idempotent. Named ``quit`` so the generic DriverBuilder disposal works
        unchanged.

        Raises:
            RuntimeError: If called from the owner thread, where submitting the
                teardown and awaiting it would deadlock. Disposal happens from a
                worker thread in normal flow.

        """
        if threading.get_ident() == self._owner_ident:
            msg = (
                "quit() called from the owner thread would deadlock. "
                "Dispose the driver from outside a page callback."
            )
            raise RuntimeError(msg)
        if self._closed:
            # Already disposed, or died: a dead transport cannot be torn down,
            # so we skip the teardown submit (it would only wedge behind the
            # stuck call) and just abandon the daemon owner thread.
            self._owner.stop()
            return
        self._closed = True

        def _teardown() -> None:
            # Tracing must be stopped (and written) before the context closes.
            if self._trace_path is not None:
                with suppress(Exception):
                    self._context.tracing.stop(path=self._trace_path)
            with suppress(Exception):
                self._context.close()
            with suppress(Exception):
                if self._browser is not None:
                    self._browser.close()
            with suppress(Exception):
                self._playwright.stop()

        # Bound the teardown: if the owner thread is wedged the future never
        # resolves, so we wait at most the call budget then walk away. stop()
        # never joins, so disposal cannot hang on a dead owner thread.
        with suppress(Exception):
            self._owner.submit(_teardown).result(timeout=self._call_timeout_s)
        self._owner.stop()
