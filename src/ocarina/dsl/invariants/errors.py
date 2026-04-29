"""Invariant errors.

This module defines exception types for invariant violations. These exceptions
are raised when validation predicates fail, allowing for structured error handling
and aggregation of multiple validation failures.

Exception hierarchy:
    InvariantViolationError (base)
    ├── DuplicatesError (for duplicate element violations)
    └── AggregateInvariantViolationError (for multiple violations)

Example:
    >>> try:
    ...     validate(data).assert_that(is_positive).execute().raise_if_invalid()
    ... except InvariantViolationError as e:
    ...     logger.error(f"Validation failed: {e}")

"""

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from collections.abc import Sequence


class InvariantViolationError(Exception):
    """Base exception raised when an invariant is violated.

    This is the base exception for all validation failures in the invariants
    system. It can be caught to handle any validation error uniformly.

    Example:
        >>> raise InvariantViolationError("Value must be positive")
        Traceback (most recent call last):
        ...
        InvariantViolationError: Value must be positive

    """


class DuplicatesError(InvariantViolationError):
    """Exception raised when duplicate elements are detected in a collection.

    This specialized error stores the duplicate values for inspection and
    generates a formatted error message listing all duplicates found.

    Attributes:
        duplicates: Sequence of duplicate values that were found.

    Example:
        >>> duplicates = ["apple", "banana"]
        >>> raise DuplicatesError(duplicates)
        Traceback (most recent call last):
        ...
        DuplicatesError: Duplicate elements detected:
         - apple
         - banana

        >>> # With custom message
        >>> raise DuplicatesError(duplicates, "Test names must be unique")
        Traceback (most recent call last):
        ...
        DuplicatesError: Test names must be unique

    """

    def __init__(self, duplicates: Sequence[Any], message: str | None = None) -> None:
        """Initialize DuplicatesError with duplicate values.

        Args:
            duplicates: Sequence of duplicate values found in the collection.
            message: Optional custom error message. If None, a default message
                    listing all duplicates will be generated.

        """
        self.duplicates = duplicates
        msg = message or "Duplicate elements detected:\n" + "\n".join(
            f" - {d}" for d in duplicates
        )
        super().__init__(msg)


class AggregateInvariantViolationError(InvariantViolationError):
    """Exception that aggregates multiple invariant violations.

    This exception is raised when multiple validation predicates fail, allowing
    all failures to be reported together rather than stopping at the first error.
    This is particularly useful in validation chains where you want to collect
    all errors before raising.

    Attributes:
        errors: Sequence of individual InvariantViolationError instances.

    Example:
        >>> errors = [
        ...     InvariantViolationError("Value must be positive"),
        ...     InvariantViolationError("Value must be less than 100")
        ... ]
        >>> raise AggregateInvariantViolationError(errors)
        Traceback (most recent call last):
        ...
        AggregateInvariantViolationError: 2 invariant violations occurred:
        > Value must be positive
        > Value must be less than 100

    Note:
        This is typically raised automatically by the validation chain's
        execute().raise_if_invalid() method when multiple assertions fail.

    """

    def __init__(self, errors: Sequence[InvariantViolationError]) -> None:
        """Initialize AggregateInvariantViolationError with multiple errors.

        Automatically formats the error message to list all violations,
        using singular or plural form based on the number of errors.

        Args:
            errors: Sequence of InvariantViolationError instances to aggregate.
                   Should contain at least one error.

        """
        self.errors = errors
        count = len(errors)
        is_plural = count > 1

        if is_plural:
            message = f"{len(errors)} invariant violations occurred:\n" + "\n".join(
                f"› {e}"  # noqa: RUF001 -> This is intentional.
                for e in errors
            )
        else:
            message = "Invariant violation occurred:\n" + "\n".join(
                f"› {e}"  # noqa: RUF001 -> This is intentional.
                for e in errors
            )

        super().__init__(message)
