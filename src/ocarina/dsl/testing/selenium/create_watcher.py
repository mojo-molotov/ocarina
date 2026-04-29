"""Create a Watcher bound to Selenium WebDriver."""

from typing import TYPE_CHECKING

from ocarina.dsl.testing.watcher import Watcher

if TYPE_CHECKING:
    from collections.abc import Callable

    from selenium.webdriver.remote.webdriver import WebDriver

type SeleniumWatcher = Watcher[WebDriver]


def create_selenium_watcher(
    *,
    callback: Callable[[SeleniumWatcher], None],
    name: str,
    poll_interval: float | None = None,
):
    """Create a Watcher bound to Selenium WebDriver."""
    return Watcher(
        callback=callback,
        name=name,
        poll_interval=poll_interval,
    )
