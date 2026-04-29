"""Selenium WebDriver factory for generic Screenshotter.

Provides a factory function to create Screenshotter instances configured
for Selenium WebDriver with optional full-page screenshot support.

Usage:
    >>> from selenium import webdriver
    >>> driver = webdriver.Chrome()
    >>> screenshotter = create_selenium_screenshotter(driver, logger)
    >>> screenshotter.take_screenshot(prefix="test")
"""

from pathlib import Path
from typing import TYPE_CHECKING, cast

from selenium.webdriver.remote.webdriver import WebDriver

from ocarina.infra.screenshotter import Screenshotter, ScreenshotterConfig
from ocarina.infra.selenium.driver_healthcheck import driver_healthcheck

if TYPE_CHECKING:
    from selenium.webdriver.firefox.webdriver import WebDriver as FirefoxWebDriver

    from ocarina.ports.ilogger import ILogger


def _selenium_save_full_page(driver: WebDriver, path: str) -> bool:
    """Save full-page screenshot if supported (Firefox only).

    This function contains Firefox-specific logic and casts. It's injected
    into the generic Screenshotter, keeping the core library clean.

    Args:
        driver: Selenium WebDriver instance.
        path: File path where screenshot should be saved.

    Returns:
        True if successful.
        False if not supported (will trigger fallback to standard screenshot).

    """
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
    """Create Screenshotter configured for Selenium WebDriver.

    Factory function that creates a Screenshotter with Selenium-specific
    configuration, including optional full-page screenshot support.

    Args:
        driver: Selenium WebDriver instance.
        logger: Logger implementing ILogger interface.
        output_dir: Directory for screenshots (default: .screenshots/).
        file_ext: File extension for screenshots (default: .png).
        default_burst_delay: Default delay between burst shots (default: 0.5s).
        enable_full_page: Enable full-page screenshots (default: True).
                         Only works on some browsers (for example: Firefox).
                         Failsafe.

    Example:
        >>> # Default config with full-page
        ... screenshotter = create_selenium_screenshotter(driver, logger)
        ... screenshotter.take_screenshot(prefix="test")

    Example:
        >>> # Disable full-page
        ... screenshotter = create_selenium_screenshotter(
        ...     driver,
        ...     logger,
        ...     enable_full_page=False,
        ... )

    Example:
        >>> # Custom config
        ... screenshotter = create_selenium_screenshotter(
        ...     driver,
        ...     logger,
        ...     output_dir=Path("/tmp/screenshots"),
        ...     file_ext=".jpg",
        ...     default_burst_delay=0.2,
        ... )

    Returns:
        Screenshotter[WebDriver] configured for Selenium.

    """
    config = ScreenshotterConfig[WebDriver](
        output_dir=output_dir or Path.cwd() / ".screenshots",
        file_ext=file_ext,
        health_check=driver_healthcheck,
        save_full_page=_selenium_save_full_page if enable_full_page else None,
        default_burst_delay=default_burst_delay,
    )

    return Screenshotter(driver, logger, config)
