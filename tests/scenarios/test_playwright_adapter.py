"""Real-browser smoke tests for the Playwright adapter.

The adapter is excluded from coverage (like the Selenium one) because it can
only be exercised against a real browser. These tests guard the genuinely novel
and risky parts of the adapter that have no equivalent in the Selenium path:

- the single-owner-thread actor (PlaywrightDriver) surviving cross-thread use,
- pool warmup handing a driver from the warmup thread to a worker thread,
- the with_timeout decorator overriding then restoring the page default,
- the title mixin and the screenshotter marshalling through the owner thread.

Skipped automatically when Playwright's Chromium browser binary is not installed,
so CI without browsers stays green.
"""

# ruff: noqa: S101

import threading
from pathlib import Path
from typing import TYPE_CHECKING

import pytest
from playwright.sync_api import sync_playwright

from ocarina.infra.playwright.create_driver import create_playwright_driver
from ocarina.infra.playwright.create_drivers_pool import (
    create_playwright_drivers_pool,
)
from ocarina.infra.playwright.create_screenshotter import (
    create_playwright_screenshotter,
)
from ocarina.infra.playwright.mixins import PlaywrightTitleMixin
from ocarina.opinionated.loggers.muted_logger import MutedLogger
from ocarina.pom.base import POMBase
from ocarina.pom.playwright.timeout import with_timeout

if TYPE_CHECKING:
    from collections.abc import Callable

    from ocarina.infra.playwright.driver import PlaywrightDriver

_WAIT_TIMEOUT_S = 10
_WAIT_TIMEOUT_MS = _WAIT_TIMEOUT_S * 1000
_OVERRIDE_TIMEOUT_S = 2


def _chromium_available() -> bool:
    try:
        with sync_playwright() as pw:
            return Path(pw.chromium.executable_path).exists()
    except Exception:  # noqa: BLE001
        return False


pytestmark = pytest.mark.skipif(
    not _chromium_available(), reason="Playwright Chromium browser not installed"
)

_PAGE_HTML = "<title>Ocarina PW</title><h1 id='t'>hello-playwright</h1>"


class _ProbePage(PlaywrightTitleMixin, POMBase):
    """Tiny page object exercising the mixin and the timeout decorator."""

    def __init__(self, driver: PlaywrightDriver) -> None:
        self._driver = driver

    def verify(self, *, timeout: float | None = None) -> _ProbePage:  # noqa: ARG002
        self._driver.submit(lambda page: page.set_content(_PAGE_HTML))
        return self

    def read_heading(self) -> str:
        return self._driver.submit(lambda page: page.inner_text("#t"))


def test_pool_warmup_then_cross_thread_use() -> None:
    """A warmed driver (built in the warmup thread) works from a worker thread."""
    pool = create_playwright_drivers_pool(
        browser="chromium", headless=True, wait_timeout=_WAIT_TIMEOUT_S, max_size=2
    )
    pool.warmup()

    captured: dict[str, str] = {}

    def worker() -> None:
        with pool.acquire() as driver:
            page = _ProbePage(driver).verify()
            captured["heading"] = page.read_heading()
            captured["title"] = page.get_current_title()

    t = threading.Thread(target=worker)
    t.start()
    t.join()
    pool.shutdown()

    assert captured["heading"] == "hello-playwright"
    assert captured["title"] == "Ocarina PW"


def test_with_timeout_overrides_then_restores() -> None:
    """The decorator sets the page default during the call and restores it after."""
    driver, dispose = _build_driver(wait_timeout=_WAIT_TIMEOUT_S)
    try:
        assert driver.default_timeout_ms == _WAIT_TIMEOUT_MS
        seen: dict[str, int] = {}

        class _Page(POMBase):
            def __init__(self, d: PlaywrightDriver) -> None:
                self._driver = d

            def verify(self, *, timeout: float | None = None) -> _Page:  # noqa: ARG002
                return self

            def get_current_title(self) -> str:
                return ""

            @with_timeout(_OVERRIDE_TIMEOUT_S)
            def step(self) -> None:
                # The configured default is tracked by the driver and must be
                # restored after the decorated call, regardless of the override.
                seen["configured"] = self._driver.default_timeout_ms

        _Page(driver).step()
        assert seen["configured"] == _WAIT_TIMEOUT_MS
        assert driver.default_timeout_ms == _WAIT_TIMEOUT_MS
    finally:
        dispose()


def test_screenshotter_writes_file(tmp_path: Path) -> None:
    """The screenshotter saves a file via the owner-thread-marshalled driver."""
    driver, dispose = _build_driver(wait_timeout=_WAIT_TIMEOUT_S)
    try:
        driver.submit(lambda page: page.set_content(_PAGE_HTML))
        shotter = create_playwright_screenshotter(
            driver, MutedLogger(), output_dir=tmp_path
        )
        shotter.take_screenshot(prefix="probe")
        assert any(tmp_path.glob("probe_*.png"))
    finally:
        dispose()


def _build_driver(
    *, wait_timeout: int
) -> tuple[PlaywrightDriver, Callable[[], None]]:
    return create_playwright_driver(
        browser="chromium", headless=True, wait_timeout=wait_timeout
    )
