"""Playwright web drivers pool."""

from ocarina.infra.drivers_pool import WebDriversPool
from ocarina.infra.playwright.driver import PlaywrightDriver

type PlaywrightDriversPool = WebDriversPool[PlaywrightDriver]
