"""Playwright WebDriversPool factory."""

import atexit
from typing import TYPE_CHECKING

from ocarina.infra.drivers_pool import WebDriversPool
from ocarina.infra.playwright.create_driver import create_playwright_driver

if TYPE_CHECKING:
    from ocarina.custom_types.playwright.supported_browsers import (
        SupportedPlaywrightBrowser,
    )
    from ocarina.custom_types.playwright.web_drivers_pool import PlaywrightDriversPool


def create_playwright_drivers_pool(  # noqa: PLR0913
    *,
    browser: SupportedPlaywrightBrowser,
    headless: bool,
    wait_timeout: int,
    max_size: int,
    profile_path: str | None = None,
    tmp_dir_prefix: str = ".playwright_profile_",
    warmup_timeout: float | None = None,
    record_video_dir: str | None = None,
    trace_dir: str | None = None,
    call_timeout: float | None = None,
) -> PlaywrightDriversPool:
    """Create a WebDriversPool backed by Playwright.

    Each driver owns a private thread (see PlaywrightDriver), so warmup is
    safe: a driver created in the warmup thread can be consumed by any worker
    thread because all Playwright calls are marshalled onto the owner thread.

    ``record_video_dir`` and ``trace_dir`` are opt-in artifact options forwarded
    to every driver in the pool (off by default). Each driver writes its own
    uniquely-named trace/video, so per-test artifacts do not collide.

    ``call_timeout`` (seconds) is the per-driver liveness ceiling: how long a
    single marshalled call may run before the driver is declared dead. It is a
    generous last-resort bound on a wedged owner thread, not a per-operation
    deadline — leave it ``None`` for the default, raise it if any single call
    (e.g. a long humanized fill) legitimately runs longer.
    """
    drivers_pool = WebDriversPool(
        create_driver=lambda: create_playwright_driver(
            browser=browser,
            headless=headless,
            wait_timeout=wait_timeout,
            profile_path=profile_path,
            tmp_dir_prefix=tmp_dir_prefix,
            record_video_dir=record_video_dir,
            trace_dir=trace_dir,
            call_timeout=call_timeout,
        ),
        max_size=max_size,
        warmup_timeout=warmup_timeout,
    )
    atexit.register(drivers_pool.shutdown)
    return drivers_pool
