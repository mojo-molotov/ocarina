"""CLI Store Singleton for Selenium."""

from ocarina.opinionated.cli.cli_store_singleton import CliStoreSingleton
from ocarina.opinionated.cli.selenium.create_cli_store import SeleniumCliStoreKeys

SeleniumCliStoreSingleton = CliStoreSingleton[SeleniumCliStoreKeys]
