"""CLI Store Singleton for Playwright."""

from ocarina.opinionated.cli.cli_store_singleton import CliStoreSingleton
from ocarina.opinionated.cli.playwright.create_cli_store import PlaywrightCliStoreKeys

PlaywrightCliStoreSingleton = CliStoreSingleton[PlaywrightCliStoreKeys]
