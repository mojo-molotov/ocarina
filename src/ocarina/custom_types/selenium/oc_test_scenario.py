"""TestScenario / TestScenarioFragment bound to Selenium's WebDriver."""

from selenium.webdriver.remote.webdriver import WebDriver

from ocarina.custom_types.oc_test import TestScenario, TestScenarioFragment

type SeleniumTestScenario = TestScenario[WebDriver]
type SeleniumTestScenarioFragment = TestScenarioFragment[WebDriver]
