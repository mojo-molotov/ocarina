"""Selenium factory for the generic Screenshotter."""

from pathlib import Path
from typing import TYPE_CHECKING, cast

from selenium.webdriver.remote.webdriver import WebDriver

from ocarina.infra.screenshotter import Screenshotter, ScreenshotterConfig
from ocarina.infra.selenium.driver_healthcheck import driver_healthcheck

if TYPE_CHECKING:
    from selenium.webdriver.firefox.webdriver import WebDriver as FirefoxWebDriver

    from ocarina.ports.ilogger import ILogger


def _selenium_save_full_page(driver: WebDriver, path: str) -> bool:
    """Full-page (Firefox only); returns False otherwise so the caller falls back."""
    if hasattr(driver, "save_full_page_screenshot"):
        return cast("FirefoxWebDriver", driver).save_full_page_screenshot(path)
    return False


def create_selenium_screenshotter(  # noqa: PLR0913
    driver: WebDriver,
    logger: ILogger,
    *,
    output_dir: Path | None = None,
    file_ext: str = ".png",
    default_burst_delay: float = 0.5,
    enable_full_page: bool = True,
) -> Screenshotter[WebDriver]:
    """Create a Screenshotter configured for Selenium WebDriver."""
    config = ScreenshotterConfig[WebDriver](
        output_dir=output_dir or Path.cwd() / ".screenshots",
        file_ext=file_ext,
        health_check=driver_healthcheck,
        save_full_page=_selenium_save_full_page if enable_full_page else None,
        default_burst_delay=default_burst_delay,
    )

    return Screenshotter(driver, logger, config)
