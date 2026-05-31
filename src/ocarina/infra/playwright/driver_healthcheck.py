"""Playwright driver liveness check via a lightweight page.title() ping."""

from typing import TYPE_CHECKING

from ocarina.custom_errors.test_framework.driver_died import DriverDiedError

if TYPE_CHECKING:
    from ocarina.infra.playwright.driver import PlaywrightDriver


def playwright_driver_healthcheck(driver: PlaywrightDriver) -> None:
    """Ping the driver to verify it is alive and responsive.

    Marshals a ``page.title()`` call onto the owner thread as a fast, stateless
    probe. Raises :class:`DriverDiedError` on any failure so callers can handle
    dead drivers uniformly.

    A voluntarily disposed driver (``driver.is_closed``) is *not* a dead
    driver: we skip the probe and return cleanly. This prevents the benign
    teardown race where a watcher callback still in flight tries to screenshot
    just after the pool has disposed the driver.

    Args:
        driver: PlaywrightDriver instance to check.

    Raises:
        DriverDiedError: If the driver is unresponsive. Original exception is chained.

    """
    if driver.is_closed:
        return
    try:
        driver.submit(lambda page: page.title())
    except Exception as exc:
        raise DriverDiedError from exc
