"""Result type for Railway Oriented Programming.

Represents computations that can succeed (Ok) or fail (Fail), making error
handling explicit in the type system.

Example:
    >>> def divide(a: int, b: int) -> Result[float]:
    ...     if b == 0:
    ...         return Fail(error=Exception("Division by zero"))
    ...     return Ok(value=a / b)
    ...
    >>> result = divide(10, 2)
    >>> if is_ok(result):
    ...     print(f"Result: {result.value}")
    >>> else:
    ...     print(f"Error: {result.error}")

"""

from dataclasses import dataclass, field
from typing import TypeGuard, final


class _BaseResult:
    """Base class ensuring both Ok and Fail have error attribute for type narrowing."""

    error: Exception | None


@final
@dataclass(frozen=True)
class Ok[T](_BaseResult):
    """Success result containing a value.

    Attributes:
        value: The successful result value of type T.
        error: Always None for Ok results.

    """

    value: T
    error: None = None


@final
@dataclass(frozen=True)
class Fail(_BaseResult):
    """Failure result containing an error.

    Attributes:
        error: The exception that caused the failure.

    """

    error: Exception = field(default_factory=lambda: Exception("Unknown error"))


type Result[T] = Ok[T] | Fail
"""Discriminated union representing success (Ok[T]) or failure (Fail).

Forces explicit error handling via type checker.
"""


def is_ok[T](result: Result[T]) -> TypeGuard[Ok[T]]:
    """Check if result is Ok, narrowing type to Ok[T]."""
    return isinstance(result, Ok)


def is_fail[T](result: Result[T]) -> TypeGuard[Fail]:
    """Check if result is Fail, narrowing type to Fail."""
    return isinstance(result, Fail)
