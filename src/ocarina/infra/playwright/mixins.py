"""Playwright POM mixins."""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ocarina.infra.playwright.driver import PlaywrightDriver


class PlaywrightTitleMixin:
    """Add ``get_current_title()`` to a POM holding ``_driver: PlaywrightDriver``."""

    _driver: PlaywrightDriver

    def get_current_title(self) -> str:
        """Return ``page.title()`` (empty if absent)."""
        return self._driver.submit(lambda page: page.title())
