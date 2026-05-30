"""Phantom Page Object Model for type-safe no-op operations (Playwright).

MutedPlaywrightPOM satisfies the POMBase interface but performs no operations.
Use it when a function requires a TPOM parameter for type consistency but
doesn't actually interact with the page (Null Object Pattern).

See Also:
    - POMBase: Base class for all page objects
    - ocarina.pom.selenium.muted.MutedPOM: Selenium counterpart

"""

from typing import TYPE_CHECKING, final

from ocarina.pom.base import POMBase

if TYPE_CHECKING:
    from ocarina.infra.playwright.driver import PlaywrightDriver


@final
class MutedPlaywrightPOM(POMBase):
    """Phantom POM — no-op placeholder that always succeeds.

    Implements POMBase purely for type compatibility. Neither verify() nor any
    other method interacts with the browser.

    Example:
        >>> phantom = MutedPlaywrightPOM(driver=driver)
        >>> phantom.verify()  # no-op, never raises

    """

    def __init__(self, *, driver: PlaywrightDriver) -> None:
        """Spawn a muted Playwright POM.

        Args:
            driver: Stored for interface compatibility, not used.

        """
        self._driver = driver

    def verify(self, *, timeout: float | None = None) -> MutedPlaywrightPOM:  # noqa: ARG002
        """No-op — always succeeds, returns self."""
        return self

    def get_current_title(self) -> str:
        """Return empty string."""
        return ""
