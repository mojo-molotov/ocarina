"""Selenium-specific type specializations for the E2E testing framework.

Monomorphic aliases derived from the generic types in custom_types.built_web_driver,
bound to Selenium's WebDriver. Import these instead of the generic types
when working with Selenium.

See Also:
    - custom_types.built_web_driver: Generic type definitions

"""

from selenium.webdriver.remote.webdriver import WebDriver

from ocarina.custom_types.built_web_driver import BuiltWebDriver

type BuiltSeleniumWebDriver = BuiltWebDriver[WebDriver]
"""BuiltWebDriver bound to Selenium's WebDriver.

Example:
    >>> def create_driver() -> BuiltSeleniumWebDriver:
    ...     driver = webdriver.Chrome()
    ...     return (driver, lambda: suppress(Exception)(driver.quit)())

"""
