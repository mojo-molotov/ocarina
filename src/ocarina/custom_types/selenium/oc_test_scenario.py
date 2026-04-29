"""Selenium-specific type specializations for the E2E testing framework.

Monomorphic aliases derived from the generic types in custom_types.oc_test,
bound to Selenium's WebDriver. Import these instead of the generic types
when working with Selenium.

See Also:
    - custom_types.oc_test: Generic type definitions

"""

from selenium.webdriver.remote.webdriver import WebDriver

from ocarina.custom_types.oc_test import TestScenario, TestScenarioFragment

type SeleniumTestScenario = TestScenario[WebDriver]
"""TestScenario bound to Selenium's WebDriver."""

type SeleniumTestScenarioFragment = TestScenarioFragment[WebDriver]
"""TestScenarioFragment bound to Selenium's WebDriver."""
