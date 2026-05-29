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
from concurrent.futures import ThreadPoolExecutor
from contextlib import suppress
from typing import TYPE_CHECKING, final

from playwright.sync_api import sync_playwright

if TYPE_CHECKING:
    from collections.abc import Callable

    from playwright.sync_api import Browser, BrowserContext, Page, Playwright

    from ocarina.custom_types.playwright.supported_browsers import (
        SupportedPlaywrightBrowser,
    )


@final
class PlaywrightDriver:
    """A Playwright session whose every call runs on a private owner thread.

    Build it via :func:`ocarina.infra.playwright.create_driver.create_playwright_driver`
    rather than directly. Page objects interact with the session exclusively
    through :meth:`submit`, which returns plain data — never live Playwright
    objects, which are owner-thread bound.
    """

    def __init__(
        self,
        *,
        browser: SupportedPlaywrightBrowser,
        headless: bool,
        wait_timeout: int,
        user_data_dir: str,
    ) -> None:
        """Spawn the owner thread and boot a persistent browser context on it.

        Args:
            browser: One of ``"chromium"``, ``"firefox"``, ``"webkit"``.
            headless: Run without a visible UI.
            wait_timeout: Default auto-wait timeout in seconds. Mapped to
                Playwright's per-page default timeout (the sync-API analogue
                of Selenium's implicit wait). Set once here; override per
                method with ``ocarina.pom.playwright.timeout.with_timeout``.
            user_data_dir: Profile directory for the persistent context
                (supplied by DriverBuilder, cleaned up on dispose).

        """
        self._default_timeout_ms = wait_timeout * 1000
        self._closed = False
        self._owner_ident: int | None = None
        self._executor = ThreadPoolExecutor(
            max_workers=1, thread_name_prefix="ocarina-pw"
        )
        self._playwright: Playwright
        self._context: BrowserContext
        self._browser: Browser | None

        self._page: Page = self._executor.submit(
            self._boot,
            browser=browser,
            headless=headless,
            user_data_dir=user_data_dir,
        ).result()

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
        self._context = browser_type.launch_persistent_context(
            user_data_dir, headless=headless
        )
        pages = self._context.pages
        page = pages[0] if pages else self._context.new_page()
        page.set_default_timeout(self._default_timeout_ms)
        page.set_default_navigation_timeout(self._default_timeout_ms)
        return page

    def submit[T](self, fn: Callable[[Page], T]) -> T:
        """Run ``fn(page)`` on the owner thread and return its result.

        This is the only sanctioned way for page objects to drive the browser.
        ``fn`` must return plain, thread-safe data (str, bool, bytes, None, ...).
        Never return live Playwright objects (Locator, ElementHandle): they are
        bound to the owner thread and unusable elsewhere.

        Re-entrancy is rejected loudly: a ``submit()`` issued from the owner
        thread (e.g. ``fn`` calling another method that submits) would queue
        behind the running task and then block on its own ``.result()`` — a
        silent deadlock. We raise instead, so the failure is named, not a hang.

        Raises:
            RuntimeError: If called after :meth:`quit`, or re-entrantly from the
                owner thread.

        """
        if self._closed:
            msg = "PlaywrightDriver has been disposed."
            raise RuntimeError(msg)
        if threading.get_ident() == self._owner_ident:
            msg = (
                "Re-entrant submit() on the owner thread would deadlock. "
                "You are already on the page thread — call page directly."
            )
            raise RuntimeError(msg)
        return self._executor.submit(lambda: fn(self._page)).result()

    @property
    def default_timeout_ms(self) -> int:
        """The configured default auto-wait timeout, in milliseconds."""
        return self._default_timeout_ms

    def set_default_timeout(self, milliseconds: int) -> None:
        """Override the page's default action/navigation timeout (marshalled)."""

        def _apply(page: Page) -> None:
            page.set_default_timeout(milliseconds)
            page.set_default_navigation_timeout(milliseconds)

        self.submit(_apply)

    def reset_default_timeout(self) -> None:
        """Restore the page default timeout to the configured value."""
        self.set_default_timeout(self._default_timeout_ms)

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
            return
        self._closed = True

        def _teardown() -> None:
            with suppress(Exception):
                self._context.close()
            with suppress(Exception):
                if self._browser is not None:
                    self._browser.close()
            with suppress(Exception):
                self._playwright.stop()

        with suppress(Exception):
            self._executor.submit(_teardown).result()
        self._executor.shutdown(wait=True)
