"""Real-browser smoke tests for the Playwright adapter.

The adapter is excluded from coverage (like the Selenium one) because it can
only be exercised against a real browser. These tests guard the genuinely novel
and risky parts of the adapter that have no equivalent in the Selenium path:

- the single-owner-thread actor (PlaywrightDriver) surviving cross-thread use,
- pool warmup handing a driver from the warmup thread to a worker thread,
- the title mixin and the screenshotter marshalling through the owner thread.

Skipped automatically when Playwright's Chromium browser binary is not installed,
so CI without browsers stays green.
"""

# ruff: noqa: S101

import threading
import time
from pathlib import Path
from typing import TYPE_CHECKING

import pytest
from playwright.sync_api import sync_playwright

from ocarina.dsl.testing.playwright.create_watcher import create_playwright_watcher
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

if TYPE_CHECKING:
    from collections.abc import Callable

    from ocarina.dsl.testing.playwright.create_watcher import PlaywrightWatcher
    from ocarina.infra.playwright.driver import PlaywrightDriver
    from ocarina.ports.ilogger import ILogger

_WATCHER_DEADLINE_S = 5.0

_WAIT_TIMEOUT_S = 10


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


def test_reentrant_submit_raises_instead_of_deadlocking() -> None:
    """A submit() issued from inside a page callback fails loud, never hangs."""
    driver, dispose = _build_driver(wait_timeout=_WAIT_TIMEOUT_S)
    try:
        with pytest.raises(RuntimeError, match="Re-entrant submit"):
            driver.submit(lambda _page: driver.submit(lambda _inner: None))
    finally:
        dispose()


def test_watcher_can_read_page_via_submit(tmp_path: Path) -> None:
    """A watcher's daemon-thread callback reads the page via submit and reports.

    Proves a Playwright watcher MAY drive reads through watcher.driver.submit
    without greenlet errors or deadlock, and that report() (which screenshots
    through ITakeScreenshot -> submit) works from the watcher thread too.
    """
    driver, dispose = _build_driver(wait_timeout=_WAIT_TIMEOUT_S)
    seen: list[str] = []
    shotter = create_playwright_screenshotter(
        driver, MutedLogger(), output_dir=tmp_path
    )

    def take_screenshot(
        _driver: PlaywrightDriver, _logger: ILogger, label: str
    ) -> None:
        shotter.take_screenshot(prefix=label)

    def callback(watcher: PlaywrightWatcher) -> None:
        title = watcher.driver.submit(lambda page: page.title())
        if title and title not in watcher.cache:
            watcher.cache.add(title)
            seen.append(title)
            watcher.report(f"watcher saw: {title}", label="PROBE")

    try:
        driver.submit(lambda page: page.set_content(_PAGE_HTML))
        watcher = create_playwright_watcher(
            callback=callback, name="probe", poll_interval=0.2
        )
        watcher.start(driver, MutedLogger(), take_screenshot)

        deadline = time.monotonic() + _WATCHER_DEADLINE_S
        while not seen and time.monotonic() < deadline:
            time.sleep(0.1)
        watcher.stop()

        assert seen == ["Ocarina PW"]
        assert any(tmp_path.glob("PROBE_*.png"))
    finally:
        dispose()


def test_trace_dir_writes_trace_zip(tmp_path: Path) -> None:
    """trace_dir produces a non-empty trace_<id>.zip on disposal."""
    driver, dispose = create_playwright_driver(
        browser="chromium",
        headless=True,
        wait_timeout=_WAIT_TIMEOUT_S,
        trace_dir=str(tmp_path),
    )
    try:
        driver.submit(lambda page: page.set_content(_PAGE_HTML))
        driver.submit(lambda page: page.click("#t"))
    finally:
        dispose()

    traces = list(tmp_path.glob("trace_*.zip"))
    assert len(traces) == 1
    assert traces[0].stat().st_size > 0


def test_video_dir_records_session(tmp_path: Path) -> None:
    """record_video_dir produces a video file once the context closes."""
    driver, dispose = create_playwright_driver(
        browser="chromium",
        headless=True,
        wait_timeout=_WAIT_TIMEOUT_S,
        record_video_dir=str(tmp_path),
    )
    try:
        driver.submit(lambda page: page.set_content(_PAGE_HTML))
        driver.submit(lambda page: page.click("#t"))
    finally:
        dispose()

    assert any(tmp_path.glob("*.webm"))


def _build_driver(*, wait_timeout: int) -> tuple[PlaywrightDriver, Callable[[], None]]:
    return create_playwright_driver(
        browser="chromium", headless=True, wait_timeout=wait_timeout
    )
