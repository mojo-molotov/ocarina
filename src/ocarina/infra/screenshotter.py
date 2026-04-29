"""Generic screenshot capture utility for test automation.

This module provides a reusable Screenshotter class that works with any
screenshot-capable driver through dependency injection.

The library is framework-agnostic and can be adapted to:
- Selenium WebDriver
- Playwright
- Puppeteer
- Any custom screenshot driver

Key features:
- Protocol-based (driver must have save_screenshot)
- Optional full-page screenshot via injection
- Generic over actual driver type
- Configurable via ScreenshotterConfig
- Thread-safe operations
- Burst mode support
- Collision-free filename generation

Usage:
    >>> # Create config for your project
    >>> config = ScreenshotterConfig[WebDriver](
    ...     output_dir=Path(".screenshots"),
    ...     file_ext=".png",
    ...     health_check=selenium_health_check,
    ...     save_full_page=selenium_save_full_page,  # Optional
    ... )
    >>> screenshotter = Screenshotter(driver, logger, config)
    >>> screenshotter.take_screenshot(prefix="test")
"""

import time
import uuid
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from threading import Lock
from typing import TYPE_CHECKING, Final, Protocol, TypeVar

if TYPE_CHECKING:
    from ocarina.ports.ilogger import ILogger


class ScreenshotDriver(Protocol):
    """Protocol for drivers with screenshot capability.

    Drivers must implement save_screenshot() method.
    Full-page screenshot is optional and injected via config.
    """

    def save_screenshot(self, path: str) -> bool:
        """Save standard viewport screenshot.

        Args:
            path: File path where screenshot should be saved.

        Returns:
            True if successful, False otherwise.

        """
        ...


TDriver = TypeVar("TDriver", bound=ScreenshotDriver)
"""Type variable for driver types implementing ScreenshotDriver protocol.

Bounded to ScreenshotDriver to ensure save_screenshot() exists,
while preserving the concrete type for health checks and full-page screenshots.
"""

HealthCheck = Callable[[TDriver], None]
"""Health check function type.

Generic over actual driver type. Allows health checks to use
driver-specific methods from the concrete driver type.

Example:
    >>> # Selenium
    ... def selenium_health_check(driver: WebDriver) -> None:
    ...     _ = driver.title  # WebDriver-specific
    ...     _ = driver.current_url  # Any WebDriver method
"""

SaveFullPageScreenshot = Callable[[TDriver, str], bool]
"""Full-page screenshot function type.

Optional function injected via config. Allows framework-specific
implementations without polluting the core library.

Example:
    >>> # Selenium Firefox
    ... def selenium_save_full_page(driver: WebDriver, path: str) -> bool:
    ...     if hasattr(driver, "save_full_page_screenshot"):
    ...         return cast(FirefoxWebDriver, driver).save_full_page_screenshot(path)
    ...     return False
"""

SCREENSHOT_SUCCESS_PREFIX: Final[str] = "Screenshot: "


@dataclass(frozen=True)
class ScreenshotterConfig[TDriver: ScreenshotDriver]:
    """Configuration for Screenshotter behavior.

    Allows each project to customize screenshot behavior without modifying
    the library code.

    Type Parameters:
        TDriver: Driver type implementing ScreenshotDriver protocol.

    Example:
        >>> # Selenium project
        ... config = ScreenshotterConfig[WebDriver](
        ...     output_dir=Path.cwd() / ".screenshots",
        ...     file_ext=".png",
        ...     health_check=selenium_health_check,
        ...     save_full_page=selenium_save_full_page,
        ... )

    Attributes:
        output_dir: Directory where screenshots are saved.
        file_ext: File extension for screenshots (e.g., ".png", ".jpg").
        health_check: Optional function to check driver health before screenshot.
        save_full_page: Optional function for full-page screenshots.
                       If None, only standard screenshots are taken.
        default_burst_delay: Default delay between burst shots in seconds.
        max_filename_retries: Max attempts to generate unique filename.
        uuid_length: Length of UUID suffix in filename.

    """

    output_dir: Path
    file_ext: str = ".png"
    health_check: HealthCheck[TDriver] | None = None
    save_full_page: SaveFullPageScreenshot[TDriver] | None = None
    default_burst_delay: float = 0.5
    max_filename_retries: int = 500
    uuid_length: int = 8


_SCREENSHOTTER_LOCK = Lock()
"""Global lock ensuring thread-safe screenshot operations.

Prevents race conditions in filename generation and file writes
across multiple threads.
"""


class Screenshotter[TDriver: ScreenshotDriver]:
    """Thread-safe screenshot capture utility.

    Generic implementation that works with any driver implementing
    ScreenshotDriver protocol. Configuration injected via ScreenshotterConfig.

    Type Parameters:
        TDriver: Driver type implementing ScreenshotDriver protocol.

    Attributes:
        _driver: Screenshot-capable driver.
        _logger: Logger for recording operations.
        _config: Configuration controlling behavior.
        _output_dir: Directory for screenshots (from config).

    Example:
        >>> config = ScreenshotterConfig[WebDriver](output_dir=Path(".screenshots"))
        >>> screenshotter = Screenshotter(driver, logger, config)
        >>> screenshotter.take_screenshot(prefix="test")

    """

    def __init__(
        self,
        driver: TDriver,
        logger: ILogger,
        config: ScreenshotterConfig[TDriver],
    ) -> None:
        """Initialize screenshotter with driver, logger, and config.

        Creates output directory if it doesn't exist.

        Args:
            driver: Driver implementing ScreenshotDriver protocol.
            logger: Logger implementing ILogger interface.
            config: Configuration for screenshotter behavior.

        """
        self._driver = driver
        self._logger = logger
        self._config = config
        self._output_dir = config.output_dir
        self._output_dir.mkdir(parents=True, exist_ok=True)

    def _generate_unique_file_path(self, *, prefix: str, counter: int) -> Path | None:
        """Generate unique screenshot filename with collision avoidance.

        Args:
            prefix: Optional prefix for filename.
            counter: Shot number in burst (-1 for single shot).

        Returns:
            Path if unique filename generated, None if all retries exhausted.

        """
        retries = self._config.max_filename_retries
        uuid_length = self._config.uuid_length
        burst = counter != -1

        for _ in range(retries):
            unique_id = uuid.uuid4().hex[:uuid_length]
            file_name = f"{prefix}_{unique_id}" if prefix else f"{unique_id}"
            base_path = self._output_dir / file_name

            normalized_file_path = (
                f"{base_path}_{counter}{self._config.file_ext}"
                if burst
                else f"{base_path}{self._config.file_ext}"
            )

            if not Path(normalized_file_path).exists():
                return Path(normalized_file_path)

        return None

    def take_screenshot(
        self,
        *,
        prefix: str = "",
        shots: int | None = None,
        burst_delay: float | None = None,
    ) -> None:
        """Capture one or more screenshots with automatic file naming.

        Thread-safe operation with optional health check and burst mode support.

        Example:
            >>> # Single shot
            ... screenshotter.take_screenshot(prefix="login")

        Example:
            >>> # Burst mode
            ... screenshotter.take_screenshot(
            ...     prefix="animation",
            ...     shots=5,
            ...     burst_delay=0.2
            ... )

        Args:
            prefix: Optional prefix for screenshot filename.
            shots: Number of screenshots to take (default: 1).
            burst_delay: Delay between burst shots in seconds
                        (default: from config).

        """
        dead_driver_msg = "Cannot take screenshot, driver died."

        def _check_driver_health() -> Exception | None:
            """Run health check if configured."""
            if self._config.health_check is None:
                return None

            try:
                self._config.health_check(self._driver)
            except Exception as exc:  # noqa: BLE001
                return exc
            return None

        dead_driver_exc = _check_driver_health()

        if dead_driver_exc:
            self._logger.exception(dead_driver_msg, exc=dead_driver_exc)
            return

        if shots is None:
            shots = 1

        if burst_delay is None:
            burst_delay = self._config.default_burst_delay

        burst = shots > 1

        with _SCREENSHOTTER_LOCK:
            for i in range(1, shots + 1):
                if burst and i > 1:
                    time.sleep(burst_delay)

                normalized_file_path = self._generate_unique_file_path(
                    prefix=prefix, counter=i if burst else -1
                )

                if normalized_file_path is None:
                    msg = (
                        "FAILED TO TAKE SCREENSHOT!"
                        " "
                        f"(Can't generate unique file path for prefix '{prefix}')"
                    )
                    self._logger.error(msg)
                    continue

                success = False
                if self._config.save_full_page is not None:
                    success = self._config.save_full_page(
                        self._driver, str(normalized_file_path)
                    )

                if not success:
                    success = self._driver.save_screenshot(str(normalized_file_path))

                if success:
                    msg = f"{SCREENSHOT_SUCCESS_PREFIX}{normalized_file_path}"
                    self._logger.info(msg)
                else:
                    dead_driver_exc = _check_driver_health()
                    if dead_driver_exc:
                        self._logger.exception(dead_driver_msg, exc=dead_driver_exc)
                        return

                    msg = f"FAILED TO TAKE SCREENSHOT! ({normalized_file_path})"
                    self._logger.error(msg)
