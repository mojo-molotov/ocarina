"""Selenium POM mixins."""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from selenium.webdriver.remote.webdriver import WebDriver


class SeleniumTitleMixin:
    """Add ``get_current_title()`` to a POM holding ``_driver: WebDriver``."""

    _driver: WebDriver

    def get_current_title(self) -> str:
        """Return ``driver.title`` (empty if absent)."""
        return self._driver.title
