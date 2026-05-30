"""Playwright-specific type specializations for the E2E testing framework.

Monomorphic alias derived from the generic type in custom_types.built_web_driver,
bound to Ocarina's PlaywrightDriver. Import this instead of the generic type
when working with Playwright.

See Also:
    - custom_types.built_web_driver: Generic type definitions
    - infra.playwright.driver.PlaywrightDriver: The concrete driver actor

"""

from ocarina.custom_types.built_web_driver import BuiltWebDriver
from ocarina.infra.playwright.driver import PlaywrightDriver

type BuiltPlaywrightDriver = BuiltWebDriver[PlaywrightDriver]
"""BuiltWebDriver bound to Ocarina's PlaywrightDriver."""
