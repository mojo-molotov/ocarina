"""Playwright factory for the generic Screenshotter.

Provides a factory function to create Screenshotter instances configured for
Ocarina's PlaywrightDriver, with full-page screenshot support.

Usage:
    >>> driver, _ = create_playwright_driver(browser="chromium", ...)
    >>> screenshotter = create_playwright_screenshotter(driver, logger)
    >>> screenshotter.take_screenshot(prefix="test")
"""

from pathlib import Path
from typing import TYPE_CHECKING

from ocarina.infra.playwright.driver import PlaywrightDriver
from ocarina.infra.playwright.driver_healthcheck import playwright_driver_healthcheck
from ocarina.infra.screenshotter import Screenshotter, ScreenshotterConfig

if TYPE_CHECKING:
    from playwright.sync_api import Page

    from ocarina.ports.ilogger import ILogger


def _playwright_save_full_page(driver: PlaywrightDriver, path: str) -> bool:
    """Save a full-page screenshot (supported natively by every Playwright browser).

    Injected into the generic Screenshotter, keeping the core library clean.

    Returns:
        True on success, False otherwise (triggers fallback to viewport shot).

    """

    def _shot(page: Page) -> bool:
        page.screenshot(path=path, full_page=True)
        return True

    try:
        return driver.submit(_shot)
    except Exception:  # noqa: BLE001 — full-page is best-effort with a fallback.
        return False


def create_playwright_screenshotter(  # noqa: PLR0913
    driver: PlaywrightDriver,
    logger: ILogger,
    *,
    output_dir: Path | None = None,
    file_ext: str = ".png",
    default_burst_delay: float = 0.5,
    enable_full_page: bool = True,
) -> Screenshotter[PlaywrightDriver]:
    """Create a Screenshotter configured for Ocarina's PlaywrightDriver.

    Args:
        driver: PlaywrightDriver instance.
        logger: Logger implementing ILogger interface.
        output_dir: Directory for screenshots (default: .screenshots/).
        file_ext: File extension for screenshots (default: .png).
        default_burst_delay: Default delay between burst shots (default: 0.5s).
        enable_full_page: Capture full-page screenshots when True (default).

    Returns:
        Screenshotter[PlaywrightDriver].

    """
    config = ScreenshotterConfig[PlaywrightDriver](
        output_dir=output_dir or Path.cwd() / ".screenshots",
        file_ext=file_ext,
        health_check=playwright_driver_healthcheck,
        save_full_page=_playwright_save_full_page if enable_full_page else None,
        default_burst_delay=default_burst_delay,
    )

    return Screenshotter(driver, logger, config)
