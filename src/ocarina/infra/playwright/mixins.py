"""Playwright-specific mixins for Page Object Model.

Optional helpers that reduce boilerplate for common Playwright operations.

Example:
    >>> class LoginPage(PlaywrightTitleMixin, POMBase):
    ...     def __init__(self, driver: PlaywrightDriver):
    ...         self._driver = driver
    ...     # get_current_title() provided by mixin

"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ocarina.infra.playwright.driver import PlaywrightDriver


class PlaywrightTitleMixin:
    """Mixin providing Playwright page title access.

    Adds get_current_title() to page objects, returning the page title via a
    marshalled ``page.title()`` call.

    Requires:
        - Subclass must have ``_driver: PlaywrightDriver`` attribute.

    """

    _driver: PlaywrightDriver
    """PlaywrightDriver instance. Must be set by subclass."""

    def get_current_title(self) -> str:
        """Get the current page title.

        Returns:
            Page title string. Empty string if no title element exists.

        """
        return self._driver.submit(lambda page: page.title())
