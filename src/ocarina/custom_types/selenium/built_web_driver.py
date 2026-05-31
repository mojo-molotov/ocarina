"""BuiltWebDriver bound to Selenium's WebDriver."""

from selenium.webdriver.remote.webdriver import WebDriver

from ocarina.custom_types.built_web_driver import BuiltWebDriver

type BuiltSeleniumWebDriver = BuiltWebDriver[WebDriver]
