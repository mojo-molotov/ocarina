"""Selenium web drivers pool."""

from selenium.webdriver.remote.webdriver import WebDriver

from ocarina.infra.drivers_pool import WebDriversPool

type SeleniumWebDriversPool = WebDriversPool[WebDriver]
