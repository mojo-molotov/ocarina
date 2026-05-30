"""Playwright driver liveness check via a lightweight page.title() ping."""

from typing import TYPE_CHECKING

from ocarina.custom_errors.test_framework.driver_died import DriverDiedError

if TYPE_CHECKING:
    from ocarina.infra.playwright.driver import PlaywrightDriver


def playwright_driver_healthcheck(driver: PlaywrightDriver) -> None:
    """Ping the driver to verify it is alive and responsive.

    Marshals a ``page.title()`` call onto the owner thread as a fast, stateless
    probe. Raises DriverDiedError on any failure so callers can handle dead
    drivers uniformly.

    Args:
        driver: PlaywrightDriver instance to check.

    Raises:
        DriverDiedError: If the driver is unresponsive. Original exception is chained.

    """
    try:
        driver.submit(lambda page: page.title())
    except Exception as exc:
        raise DriverDiedError from exc
