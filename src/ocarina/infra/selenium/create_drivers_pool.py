"""Selenium WebDriversPool factory."""

import atexit
from typing import TYPE_CHECKING

from ocarina.infra.drivers_pool import WebDriversPool
from ocarina.infra.selenium.create_driver import create_selenium_driver

if TYPE_CHECKING:
    from ocarina.custom_types.selenium.supported_browsers import (
        SupportedSeleniumBrowser,
    )
    from ocarina.custom_types.selenium.web_drivers_pool import SeleniumWebDriversPool


def create_selenium_drivers_pool(  # noqa: PLR0913
    *,
    browser: SupportedSeleniumBrowser,
    driver_path: str,
    headless: bool,
    wait_timeout: int,
    max_size: int,
    profile_path: str | None = None,
    tmp_dir_prefix: str = ".webdriver_profile_",
    warmup_timeout: float | None = None,
) -> SeleniumWebDriversPool:
    """Create a WebDriversPool backed by Selenium WebDriver."""
    drivers_pool = WebDriversPool(
        create_driver=lambda: create_selenium_driver(
            browser=browser,
            driver_path=driver_path,
            headless=headless,
            wait_timeout=wait_timeout,
            profile_path=profile_path,
            tmp_dir_prefix=tmp_dir_prefix,
        ),
        max_size=max_size,
        warmup_timeout=warmup_timeout,
    )
    atexit.register(drivers_pool.shutdown)
    return drivers_pool
