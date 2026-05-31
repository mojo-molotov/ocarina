"""TestScenario / TestScenarioFragment bound to PlaywrightDriver."""

from ocarina.custom_types.oc_test import TestScenario, TestScenarioFragment
from ocarina.infra.playwright.driver import PlaywrightDriver

type PlaywrightTestScenario = TestScenario[PlaywrightDriver]
type PlaywrightTestScenarioFragment = TestScenarioFragment[PlaywrightDriver]
