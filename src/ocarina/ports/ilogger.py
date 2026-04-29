"""Logger interface (port).

This module defines ILogger, the abstract interface for logging in the test
framework. It provides structured logging with taxonomy, lazy prefixes, and
multiple severity levels.

The interface supports:
- Lazy prefix evaluation via Thunk
- Domain taxonomy for log categorization
- Multiple severity levels (debug, info, warning, error, critical)
- Custom test-specific levels (test_name, success)
- Exception logging with context
- Raw output for unformatted logging
- Cleanup via context manager protocol

Example:
    >>> class ConsoleLogger(ILogger):
    ...     def info(self, msg: str, *args: object, **kwargs: object) -> None:
    ...         print(f"INFO: {msg}")
    ...
    >>> with ConsoleLogger() as logger:
    ...     logger.info("Test started")
    ...     # Cleanup automatic on exit

"""

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Self

if TYPE_CHECKING:
    from ocarina.custom_types.supports_write import SupportsWrite
    from ocarina.custom_types.thunk import Thunk


class ILogger(ABC):
    """Abstract logger interface for test framework.

    Defines the contract for logging implementations with support for
    structured logging, lazy prefixes, domain taxonomy, and multiple
    severity levels.

    Implementations must provide:
    - Severity methods (debug, info, warning, error, critical, exception)
    - Test-specific methods (test_name, success)
    - Configuration (set_prefix, set_domain_taxonomy)
    - Raw output (raw)
    - Cleanup (context manager protocol)

    Example:
        >>> class MyLogger(ILogger):
        ...     def info(self, msg: str, *args: object, **kwargs: object) -> None:
        ...         print(msg)
        ...     # Implement other abstract methods...

    """

    @abstractmethod
    def set_prefix(self, prefix_thunk: Thunk[str]) -> Self:
        """Set lazy prefix for log messages.

        Args:
            prefix_thunk: Thunk returning prefix string, evaluated per log call.

        Returns:
            Self for method chaining.

        Example:
            >>> logger.set_prefix(lambda: f"[{datetime.now()}]")

        """
        ...

    @abstractmethod
    def set_domain_taxonomy(self, taxonomy: tuple[str, ...]) -> Self:
        """Set domain taxonomy for log categorization.

        Args:
            taxonomy: Hierarchical domain path (e.g., ("unit", "pom", "selenium")).

        Returns:
            Self for method chaining.

        Example:
            >>> logger.set_domain_taxonomy(("integration", "api", "auth"))

        """
        ...

    @abstractmethod
    def raw(
        self,
        *args: object,
        stream: SupportsWrite[str] | None = None,
        **kwargs: object,
    ) -> None:
        """Write raw unformatted output.

        Args:
            *args: Objects to write (converted to strings).
            stream: Output stream (default: implementation-specific).
            **kwargs: Additional implementation-specific options.

        Example:
            >>> logger.raw("Unformatted", "output")

        """
        ...

    @abstractmethod
    def critical(
        self, msg: str, *args: object, exc: Exception | None = None, **kwargs: object
    ) -> None:
        """Log critical-level message.

        Args:
            msg: Log message.
            *args: Additional context objects.
            exc: Optional exception to include.
            **kwargs: Additional implementation-specific options.

        """
        ...

    @abstractmethod
    def error(
        self, msg: str, *args: object, exc: Exception | None = None, **kwargs: object
    ) -> None:
        """Log error-level message.

        Args:
            msg: Log message.
            *args: Additional context objects.
            exc: Optional exception to include.
            **kwargs: Additional implementation-specific options.

        """
        ...

    @abstractmethod
    def warning(
        self, msg: str, *args: object, exc: Exception | None = None, **kwargs: object
    ) -> None:
        """Log warning-level message.

        Args:
            msg: Log message.
            *args: Additional context objects.
            exc: Optional exception to include.
            **kwargs: Additional implementation-specific options.

        """
        ...

    @abstractmethod
    def info(
        self, msg: str, *args: object, exc: Exception | None = None, **kwargs: object
    ) -> None:
        """Log info-level message.

        Args:
            msg: Log message.
            *args: Additional context objects.
            exc: Optional exception to include.
            **kwargs: Additional implementation-specific options.

        """
        ...

    @abstractmethod
    def debug(
        self, msg: str, *args: object, exc: Exception | None = None, **kwargs: object
    ) -> None:
        """Log debug-level message.

        Args:
            msg: Log message.
            *args: Additional context objects.
            exc: Optional exception to include.
            **kwargs: Additional implementation-specific options.

        """
        ...

    @abstractmethod
    def test_name(
        self, msg: str, *args: object, exc: Exception | None = None, **kwargs: object
    ) -> None:
        """Log test name (custom level for test identification).

        Args:
            msg: Test name or description.
            *args: Additional context objects.
            exc: Optional exception to include.
            **kwargs: Additional implementation-specific options.

        """
        ...

    @abstractmethod
    def success(
        self, msg: str, *args: object, exc: Exception | None = None, **kwargs: object
    ) -> None:
        """Log success message (custom level for test assertions).

        Args:
            msg: Success message.
            *args: Additional context objects.
            exc: Optional exception to include.
            **kwargs: Additional implementation-specific options.

        """
        ...

    @abstractmethod
    def exception(
        self, msg: str, *args: object, exc: Exception | None = None, **kwargs: object
    ) -> None:
        """Log exception with full traceback.

        Args:
            msg: Exception context message.
            *args: Additional context objects.
            exc: Exception to log (if None, uses sys.exc_info()).
            **kwargs: Additional implementation-specific options.

        """
        ...

    @abstractmethod
    def cleanup(self) -> None:
        """Cleanup effect."""
        ...
