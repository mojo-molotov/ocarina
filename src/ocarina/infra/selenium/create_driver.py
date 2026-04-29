"""Selenium WebDriver builder."""

from pathlib import Path
from typing import TYPE_CHECKING, Any

from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.webdriver import WebDriver as Chrome
from selenium.webdriver.edge.options import Options as EdgeOptions
from selenium.webdriver.edge.service import Service as EdgeService
from selenium.webdriver.edge.webdriver import WebDriver as Edge
from selenium.webdriver.firefox.firefox_profile import FirefoxProfile
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.webdriver.firefox.service import Service as FirefoxService
from selenium.webdriver.firefox.webdriver import WebDriver as Firefox
from selenium.webdriver.safari.webdriver import WebDriver as Safari

from ocarina.dsl.invariants.assertions import is_in
from ocarina.dsl.invariants.validate import validate
from ocarina.infra.driver_builder import DriverBuilder

if TYPE_CHECKING:
    from collections.abc import Callable

    from selenium.webdriver.remote.webdriver import WebDriver

    from ocarina.custom_types.selenium.built_web_driver import BuiltSeleniumWebDriver
    from ocarina.custom_types.selenium.supported_browsers import (
        SupportedSeleniumBrowser,
    )


def _build_firefox(
    *, profile_path: str | None, driver_path: str, headless: bool, wait_timeout: int
) -> WebDriver:
    service = FirefoxService(executable_path=driver_path)
    options = FirefoxOptions()

    if headless:
        options.add_argument("-headless")

    if profile_path:
        options.profile = FirefoxProfile(profile_path)  # type: ignore[no-untyped-call]

    driver = Firefox(service=service, options=options)
    driver.implicitly_wait(wait_timeout)
    return driver


def _build_chrome(
    *, profile_path: str | None, driver_path: str, headless: bool, wait_timeout: int
) -> WebDriver:
    service = ChromeService(executable_path=driver_path)
    options = ChromeOptions()

    if headless:
        options.add_argument("--headless=new")

    if profile_path:
        options.add_argument(f"--user-data-dir={profile_path}")

    driver = Chrome(service=service, options=options)
    driver.implicitly_wait(wait_timeout)
    return driver


def _build_edge(
    *, profile_path: str | None, driver_path: str, headless: bool, wait_timeout: int
) -> WebDriver:
    service = EdgeService(executable_path=driver_path)
    options = EdgeOptions()

    if headless:
        options.add_argument("--headless=new")

    if profile_path:
        options.add_argument(f"--user-data-dir={profile_path}")

    driver = Edge(service=service, options=options)
    driver.implicitly_wait(wait_timeout)
    return driver


def _build_safari(*, wait_timeout: int) -> WebDriver:
    driver = Safari()
    driver.implicitly_wait(wait_timeout)
    return driver


def create_selenium_driver(  # noqa: PLR0913
    *,
    browser: SupportedSeleniumBrowser,
    driver_path: str,
    headless: bool,
    wait_timeout: int,
    profile_path: str | None = None,
    tmp_dir_prefix: str = ".webdriver_profile_",
) -> BuiltSeleniumWebDriver:
    """Create a Selenium WebDriver wrapped in a BuiltWebDriver tuple.

    Note:
        Safari uses the native macOS safaridriver — driver_path, profile_path,
        and headless are ignored (Safari does not support headless mode).
        Enable Remote Automation in Safari > Dev    elop menu first.

    """
    resolved_driver_path = (
        str(Path(driver_path).resolve()) if browser != "safari" else ""
    )

    builders: dict[SupportedSeleniumBrowser, Callable[[Any], WebDriver]] = {
        "firefox": lambda _profile_path: _build_firefox(
            profile_path=_profile_path,
            driver_path=resolved_driver_path,
            headless=headless,
            wait_timeout=wait_timeout,
        ),
        "chrome": lambda _profile_path: _build_chrome(
            profile_path=_profile_path,
            driver_path=resolved_driver_path,
            headless=headless,
            wait_timeout=wait_timeout,
        ),
        "edge": lambda _profile_path: _build_edge(
            profile_path=_profile_path,
            driver_path=resolved_driver_path,
            headless=headless,
            wait_timeout=wait_timeout,
        ),
        "safari": lambda _profile_path: _build_safari(
            wait_timeout=wait_timeout,
        ),
    }

    validate(browser, name="browser").assert_that(
        is_in(builders)
    ).execute().raise_if_invalid()

    return DriverBuilder(
        build_driver=builders[browser],
        profile_path=profile_path,
        tmp_dir_prefix=tmp_dir_prefix,
    ).build()
