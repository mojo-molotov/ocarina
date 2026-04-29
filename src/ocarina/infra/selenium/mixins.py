"""Selenium-specific mixins for Page Object Model.

This module provides Selenium-specific functionality that can be mixed
into POM classes. These mixins are optional helpers that reduce boilerplate
for common Selenium operations.

Example:
    >>> class LoginPage(SeleniumTitleMixin, POMBase):
    ...     def __init__(self, driver: WebDriver):
    ...         self._driver = driver
    ...     # get_current_title() provided by mixin

"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from selenium.webdriver.remote.webdriver import WebDriver


class SeleniumTitleMixin:
    """Mixin providing Selenium page title access.

    Adds get_current_title() method to page objects, returning the browser's
    current page title via WebDriver.title property.

    Requires:
        - Subclass must have _driver: WebDriver attribute

    Example:
        >>> class LoginPage(SeleniumTitleMixin, POMBase):
        ...     def __init__(self, driver: WebDriver):
        ...         self._driver = driver  # Required by mixin
        ...
        ...     def verify(self, timeout: float | None = None) -> Self:
        ...         # Can use get_current_title() in verification
        ...         if "Login" not in self.get_current_title():
        ...             raise PageVerificationError("Not on login page")
        ...         return self

    Note:
        This is a convenience mixin. Page objects can access driver.title
        directly without using this mixin if preferred.

    """

    _driver: WebDriver
    """WebDriver instance. Must be set by subclass."""

    def get_current_title(self) -> str:
        """Get the current page title from Selenium WebDriver.

        Returns:
            Page title string. Empty string if no title element exists.

        Example:
            >>> page = LoginPage(driver)
            >>> title = page.get_current_title()
            >>> assert "Login" in title

        """
        return self._driver.title
