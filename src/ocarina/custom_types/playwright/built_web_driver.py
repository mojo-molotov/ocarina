"""BuiltWebDriver bound to PlaywrightDriver."""

from ocarina.custom_types.built_web_driver import BuiltWebDriver
from ocarina.infra.playwright.driver import PlaywrightDriver

type BuiltPlaywrightDriver = BuiltWebDriver[PlaywrightDriver]
