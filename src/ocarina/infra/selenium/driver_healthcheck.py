"""WebDriver liveness check via a lightweight driver.title ping."""

from typing import TYPE_CHECKING

from ocarina.custom_errors.test_framework.driver_died import DriverDiedError

if TYPE_CHECKING:
    from selenium.webdriver.remote.webdriver import WebDriver


def driver_healthcheck(driver: WebDriver) -> None:
    """Ping the WebDriver to verify it is alive and responsive.

    Uses driver.title as a fast, stateless probe. Raises DriverDiedError
    on any failure so callers can handle dead drivers uniformly.

    Args:
        driver: WebDriver instance to check.

    Raises:
        DriverDiedError: If the driver is unresponsive. Original exception is chained.

    Example:
        >>> try:
        ...     driver_healthcheck(driver)
        ... except DriverDiedError:
        ...     driver = recreate_driver()

    """
    try:
        driver.title  # noqa: B018 — ping only, no assignment intended.
    except Exception as exc:
        raise DriverDiedError from exc
