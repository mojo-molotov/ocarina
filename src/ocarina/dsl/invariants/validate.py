"""Fluent validation chain using Railway Oriented Programming.

Supports sequential assertions, error aggregation, alternative predicates
(.otherwise()), and value transformation (.then()).

Basic usage:
    >>> validate(email, name="email")
    ...     .assert_that(is_str)
    ...     .assert_that(is_email)
    ...     .execute()
    ...     .raise_if_invalid()

With alternatives:
    >>> validate(age, name="age")
    ...     .assert_that(is_equal_to(18), msg="Must be 18 or at most 65")
    ...     .otherwise(is_less_than_or_equal_to(65), msg="Must be 18 or at most 65")
    ...     .execute()
    ...     .raise_if_invalid()

With chained values:
    >>> validate(user, name="user")
    ...     .assert_that(is_not_none)
    ...     .then(user.email, name="user.email")
    ...     .assert_that(is_email)
    ...     .execute()
    ...     .raise_if_invalid()

See Also:
    - dsl.invariants.internals.validation_chain: Architecture and type flow details

"""

from collections.abc import Callable
from typing import final

from ocarina.dsl.invariants.internals.validation_chain import (
    ValidationAssertBlock,
    ValidationStartBlock,
)

type Predicate[T] = Callable[[T], None]

type ValidationChainBuilder[T] = Callable[
    [ValidationStartBlock[T]], ValidationAssertBlock[T]
]


def _create_business_invariant_validator[T](
    value: T,
    name: str,
    build_chain: ValidationChainBuilder[T],
) -> ValidationAssertBlock[T]:
    """Create custom invariant validators.

    Args:
        value: The value to validate.
        name: Name for error messages.
        build_chain: Function that builds the validation chain.

    Returns:
        The completed validation chain.

    """
    start_block = validate(value, name=name)
    return build_chain(start_block)


def validate[T](value: T, *, name: str | None = None) -> ValidationStartBlock[T]:
    """Entry point for creating a chainable validation.

    Args:
        value: The value to validate.
        name: Optional name for this value in error messages (e.g., "email", "age").

    Returns:
        A ValidationStartBlock ready to accept assertions.

    Example:
        >>> # Simple validation
        >>> validate(42).assert_that(is_positive).execute().raise_if_invalid()

        >>> # Named validation
        >>> validate(email, name="email")
        ...     .assert_that(is_str)
        ...     .assert_that(is_email)
        ...     .execute()
        ...     .raise_if_invalid()

    """
    return ValidationStartBlock(value, name=name)


class _BaseCustomInvariantValidator:
    """Base class for creating domain-specific invariant validators.

    This provides a factory pattern for creating reusable, composable
    validation functions with consistent error handling.
    """

    @staticmethod
    def create[T](
        value: T,
        name: str,
        build_chain: Callable[[ValidationStartBlock[T], T], ValidationAssertBlock[T]],
    ) -> ValidationAssertBlock[T]:
        """Create a custom invariant validator.

        Args:
            value: The value to validate.
            name: Name for error messages.
            build_chain: Function that builds the val···idation chain, receiving
                        both the start block and the value.

        Returns:
            The completed validation chain.

        """
        return _create_business_invariant_validator(
            value, name, lambda chain: build_chain(chain, value)
        )


@final
class BusinessInvariantValidator(_BaseCustomInvariantValidator):
    """Factory for creating business domain invariant validators.

    Use this for domain-specific validation logic (e.g., "user must be adult",
    "order total must match items").

    """


@final
class FrameworkInvariantValidator(_BaseCustomInvariantValidator):
    """Factory for creating framework-level invariant validators.

    Use this for technical/framework validation logic (e.g., "config must be valid",
    "test structure must be correct").

    """
