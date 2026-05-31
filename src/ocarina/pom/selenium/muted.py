"""Phantom POM for Selenium — Null Object satisfying POMBase."""

from typing import TYPE_CHECKING, final

from ocarina.pom.base import POMBase

if TYPE_CHECKING:
    from selenium.webdriver.remote.webdriver import WebDriver


@final
class MutedPOM(POMBase):
    """No-op POM that satisfies POMBase for type consistency."""

    def __init__(self, *, driver: WebDriver) -> None:
        """Store the driver (unused) for interface compatibility."""
        self._driver = driver

    def verify(self, *, timeout: float | None = None) -> MutedPOM:  # noqa: ARG002
        """No-op."""
        return self

    def get_current_title(self) -> str:
        """Return empty string."""
        return ""
