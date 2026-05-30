"""Playwright-specific type specializations for the E2E testing framework.

Monomorphic aliases derived from the generic types in custom_types.oc_test,
bound to Ocarina's PlaywrightDriver. Import these instead of the generic types
when working with Playwright.

See Also:
    - custom_types.oc_test: Generic type definitions

"""

from ocarina.custom_types.oc_test import TestScenario, TestScenarioFragment
from ocarina.infra.playwright.driver import PlaywrightDriver

type PlaywrightTestScenario = TestScenario[PlaywrightDriver]
"""TestScenario bound to Ocarina's PlaywrightDriver."""

type PlaywrightTestScenarioFragment = TestScenarioFragment[PlaywrightDriver]
"""TestScenarioFragment bound to Ocarina's PlaywrightDriver."""
