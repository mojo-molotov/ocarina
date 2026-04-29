"""Driver lifecycle failure errors.

Defines exceptions for WebDriver instances that die or become unresponsive
during test execution.

Common causes:
- Browser crash or forced termination
- Network disconnection (remote WebDriver)
- WebDriver command timeout
- OS killing browser process (OOM, resource limits)

Example:
    >>> try:
    ...     process_something(...)
    ... except DriverDiedError:
    ...     logger.error("WebDriver died!")

"""

from typing import final


@final
class DriverDiedError(Exception):
    """Raised when a WebDriver instance dies or becomes unresponsive.

    Indicates the WebDriver is no longer usable and cannot execute commands.
    The driver should be disposed and a new instance created to continue.

    Typical causes:
    - Browser process crashed or killed
    - WebDriver connection lost (remote drivers)
    - Critical error corrupting driver state
    - System resource exhaustion (OOM)

    Note:
        Typically caught at high level (WebDriversPool, test runner) for
        driver replacement and retry logic, not in individual test steps.

    Example:
        >>> def healthcheck(driver: WebDriver) -> None:
        ...     try:
        ...         _ = driver.title  # Liveness check
        ...     except Exception as exc:
        ...         raise DriverDiedError("Driver unresponsive") from exc

    """
