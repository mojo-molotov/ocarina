"""Invariants assertions.

This module provides composable validation predicates for building validation chains.
Each invariant is a predicate function that raises an InvariantViolationError
when the condition is not met.

Predicates can be composed using the validation chain DSL:
    validate(email, name="email")
        .assert_that(is_str)
        .assert_that(is_email)
        .execute()
        .raise_if_invalid()

Higher-order predicates (those that return predicates) allow for parameterized
validation:
    validate(age, name="age")
        .assert_that(is_equal_to(18))
        .otherwise(is_less_than_or_equal_to(65))
        .execute()
        .raise_if_invalid()
"""

from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any

from .errors import (
    DuplicatesError,
    InvariantViolationError,
)

if TYPE_CHECKING:
    from collections.abc import Callable, Iterable, Sized

    from .validate import Predicate


def is_str(value: Any) -> None:  # noqa: ANN401
    """Assert that value is a string.

    Args:
        value: The value to check.

    Raises:
        InvariantViolationError: If value is not a string.

    Example:
        >>> is_str("hello")  # OK
        >>> is_str(42)  # Raises InvariantViolationError

    """
    if not isinstance(value, str):
        msg = "Expected value to be string."
        raise InvariantViolationError(msg)


def is_none(value: Any) -> None:  # noqa: ANN401
    """Assert that value is None.

    Args:
        value: The value to check.

    Raises:
        InvariantViolationError: If value is not None.

    Example:
        >>> is_none(None)  # OK
        >>> is_none(42)  # Raises InvariantViolationError

    """
    if value is not None:
        msg = f"Expected None, got {value!r}."
        raise InvariantViolationError(msg)


def is_not_none(value: Any) -> None:  # noqa: ANN401
    """Assert that value is not None.

    Args:
        value: The value to check.

    Raises:
        InvariantViolationError: If value is None.

    Example:
        >>> is_not_none(42)  # OK
        >>> is_not_none(None)  # Raises InvariantViolationError

    """
    if value is None:
        msg = "Expected value not to be None."
        raise InvariantViolationError(msg)


def is_equal_to(cmp: Any) -> Predicate[Any]:  # noqa: ANN401
    """Create a predicate that asserts value equals the comparison value.

    This is a higher-order function that returns a predicate configured
    with a specific comparison value.

    Args:
        cmp: The value to compare against.

    Returns:
        A predicate function that checks equality.

    Raises:
        InvariantViolationError: If value != cmp (raised by returned predicate).

    Example:
        >>> check_is_five = is_equal_to(5)
        >>> check_is_five(5)  # OK
        >>> check_is_five(3)  # Raises InvariantViolationError

    """

    def unwrapped(value: Any) -> None:  # noqa: ANN401
        if value != cmp:
            msg = f"{value} is not equal to {cmp}."
            raise InvariantViolationError(msg)

    return unwrapped


def is_less_than_or_equal_to(cmp: float) -> Predicate[float]:
    """Create a predicate that asserts value <= comparison value.

    Args:
        cmp: The upper bound (inclusive).

    Returns:
        A predicate function that checks the bound.

    Raises:
        InvariantViolationError: If value > cmp (raised by returned predicate).

    Example:
        >>> check_max_100 = is_less_than_or_equal_to(100)
        >>> check_max_100(50)  # OK
        >>> check_max_100(150)  # Raises InvariantViolationError

    """

    def unwrapped(value: float) -> None:
        if value > cmp:
            msg = f"{value} is not less than or equal to {cmp}."
            raise InvariantViolationError(msg)

    return unwrapped


def is_positive(value: float) -> None:
    """Assert that value is positive (>= 0).

    Args:
        value: The numeric value to check.

    Raises:
        InvariantViolationError: If value < 0.

    Example:
        >>> is_positive(42)  # OK
        >>> is_positive(0)  # OK
        >>> is_positive(-1)  # Raises InvariantViolationError

    """
    if value < 0:
        msg = f"Expected positive number, got {value}."
        raise InvariantViolationError(msg)


def is_not_zero(value: float) -> None:
    """Assert that value is not zero.

    Args:
        value: The numeric value to check.

    Raises:
        InvariantViolationError: If value == 0.

    Example:
        >>> is_not_zero(42)  # OK
        >>> is_not_zero(-1)  # OK
        >>> is_not_zero(0)  # Raises InvariantViolationError

    """
    if value == 0:
        msg = "Value must not be zero."
        raise InvariantViolationError(msg)


def is_in(elements: Iterable[Any]) -> Predicate[Any]:
    """Create a predicate that asserts value is in the given collection.

    Args:
        elements: The collection of allowed values.

    Returns:
        A predicate function that checks membership.

    Raises:
        InvariantViolationError: If value not in elements.

    Example:
        >>> check_color = is_in(["red", "green", "blue"])
        >>> check_color("red")  # OK
        >>> check_color("yellow")  # Raises InvariantViolationError

    """
    elms = tuple(elements)

    def unwrapped(value: Any) -> None:  # noqa: ANN401
        if value not in elms:
            pretty_elms = ", ".join(map(str, elms))
            msg = f"Value {value!r} must be in: {pretty_elms}."
            raise InvariantViolationError(msg)

    return unwrapped


def is_file(value: str | Path) -> None:
    """Assert that the path points to an existing file.

    Args:
        value: A file path (string or Path object).

    Raises:
        InvariantViolationError: If the path doesn't point to a file.

    Example:
        >>> is_file("/path/to/existing/file.txt")  # OK
        >>> is_file("/path/to/directory")  # Raises InvariantViolationError

    """
    if not Path(value).is_file():
        msg = f"'{value}' does not point to a file."
        raise InvariantViolationError(msg)


def is_dir(value: str | Path) -> None:
    """Assert that the path points to an existing directory.

    Args:
        value: A directory path (string or Path object).

    Raises:
        InvariantViolationError: If the path doesn't point to a directory.

    Example:
        >>> is_dir("/path/to/directory")  # OK
        >>> is_dir("/path/to/file.txt")  # Raises InvariantViolationError

    """
    if not Path(value).is_dir():
        msg = f"'{value}' does not point to a directory."
        raise InvariantViolationError(msg)


def is_iso_date_string(value: str) -> None:
    """Assert that the string is a valid ISO 8601 date string.

    Args:
        value: The string to validate.

    Raises:
        InvariantViolationError: If the string is not a valid ISO date.

    Example:
        >>> is_iso_date_string("2025-12-18")  # OK
        >>> is_iso_date_string("2025-12-18T10:30:00Z")  # OK
        >>> is_iso_date_string("invalid")  # Raises InvariantViolationError

    """
    try:
        datetime.fromisoformat(value)
    except Exception as exc:
        msg = f"'{value}' is not a valid ISO date string."
        raise InvariantViolationError(msg) from exc


def is_iso_utc_date_string(value: str) -> None:
    """Assert that the string is a valid ISO 8601 UTC date string.

    The date must be in UTC timezone (not just a valid ISO date).

    Args:
        value: The string to validate.

    Raises:
        InvariantViolationError: If the string is not a valid UTC ISO date.

    Example:
        >>> is_iso_utc_date_string("2025-12-18T10:30:00+00:00")  # OK
        >>> is_iso_utc_date_string("2025-12-18T10:30:00Z")  # OK
        >>> is_iso_utc_date_string("2025-12-18T10:30:00+02:00")  # Not UTC, raises error
        >>> is_iso_utc_date_string("2025-12-18")  # No timezone, raises error

    """
    try:
        dt = datetime.fromisoformat(value)
    except Exception as exc:
        msg = f"'{value}' is not a valid ISO date string."
        raise InvariantViolationError(msg) from exc

    if dt.tzinfo != UTC:
        msg = f"'{value}' is not in UTC (tz={dt.tzinfo})."
        raise InvariantViolationError(msg)


def is_email(value: str) -> None:
    """Assert that the string is a valid email address (fast check)."""
    if " " in value:
        msg = f"'{value}' must not contain whitespace."
        raise InvariantViolationError(msg)

    if value.count("@") != 1:
        msg = f"'{value}' must contain exactly one '@' character."
        raise InvariantViolationError(msg)

    local_part, domain_part = value.split("@")
    if not local_part or not domain_part:
        msg = f"'{value}' must have non-empty local and domain parts."
        raise InvariantViolationError(msg)

    if "." not in domain_part:
        msg = f"Domain part of '{value}' must contain at least one '.'."
        raise InvariantViolationError(msg)


def has_unique_elements(
    *,
    key: Callable[[Any], Any] | None = None,
):
    """Create a predicate that asserts all elements in a collection are unique.

    Uses strict type checking: 1, 1.0, and True are considered different values.
    Supports unhashable types (lists, dicts, sets) by comparing them directly.

    Args:
        key: Optional function to extract comparison key from each element.
             If None, elements are compared directly.

    Returns:
        A predicate function that checks uniqueness.

    Raises:
        DuplicatesError: If duplicates are found (raised by returned predicate).

    Example:
        >>> check_unique = has_unique_elements()
        >>> check_unique([1, 2, 3])  # OK
        >>> check_unique([1, 2, 2, 3])  # Raises DuplicatesError
        >>> check_unique([[1, 2], [3, 4]])  # OK (unhashable types supported)

    """

    def unwrapped(value: Iterable[Any]) -> None:
        items = list(value)
        key_fn = key or (lambda x: x)

        seen: list[tuple[type, Any]] = []
        duplicates = []

        for item in items:
            keyed = key_fn(item)
            typed_key = (type(keyed), keyed)

            found = False
            for seen_key in seen:
                if typed_key[0] == seen_key[0] and typed_key[1] == seen_key[1]:
                    found = True
                    if keyed not in duplicates:
                        duplicates.append(keyed)
                    break

            if not found:
                seen.append(typed_key)

        if duplicates:
            raise DuplicatesError(duplicates)

    return unwrapped


def is_empty(value: Sized) -> None:
    """Assert that the collection is empty.

    Args:
        value: Any collection with a length (list, dict, string, etc.).

    Raises:
        InvariantViolationError: If the collection is not empty.

    Example:
        >>> is_empty([])  # OK
        >>> is_empty("")  # OK
        >>> is_empty([1, 2, 3])  # Raises InvariantViolationError

    """
    if len(value) != 0:
        msg = "Value must be empty."
        raise InvariantViolationError(msg)


def is_truthy(value: Any) -> None:  # noqa: ANN401 -> This is intentional.
    """Assert that value is truthy in Python's boolean context.

    Args:
        value: The value to check.

    Raises:
        InvariantViolationError: If value is falsy (False, None, 0, "", [], etc.).

    Example:
        >>> is_truthy(42)  # OK
        >>> is_truthy("hello")  # OK
        >>> is_truthy([1])  # OK
        >>> is_truthy(0)  # Raises InvariantViolationError
        >>> is_truthy("")  # Raises InvariantViolationError
        >>> is_truthy([])  # Raises InvariantViolationError

    """
    if not value:
        msg = "Value must be truthy."
        raise InvariantViolationError(msg)
