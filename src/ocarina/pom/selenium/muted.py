"""Phantom Page Object Model for type-safe no-op operations.

MutedPOM satisfies the POMBase interface but performs no operations.
Use it when a function requires a TPOM parameter for type consistency
but doesn't actually interact with the page — avoiding Optional[TPOM]
and None checks everywhere (Null Object Pattern).

See Also:
    - POMBase: Base class for all page objects
    - TPOM: Generic type variable for page objects

"""

from typing import TYPE_CHECKING, final

from ocarina.pom.base import POMBase

if TYPE_CHECKING:
    from selenium.webdriver.remote.webdriver import WebDriver


@final
class MutedPOM(POMBase):
    """Phantom POM — no-op placeholder that always succeeds.

    Implements POMBase purely for type compatibility. Neither verify()
    nor any other method interacts with the browser.

    Example:
        >>> phantom = MutedPOM(driver=driver)
        >>> phantom.verify()  # no-op, never raises

    """

    def __init__(self, *, driver: WebDriver) -> None:
        """Spawn a muted Selenium POM.

        Args:
            driver: Stored for interface compatibility, not used.

        """
        self._driver = driver

    def verify(self, *, timeout: float | None = None) -> MutedPOM:  # noqa: ARG002
        """No-op — always succeeds, returns self."""
        return self

    def get_current_title(self) -> str:
        """Return empty string."""
        return ""
