"""Validation chain core.

Architecture:
    ValidationStartBlock: Entry point, awaits first assertion.
    ValidationAssertBlock: Accepts more assertions, alternatives, or execution.
    _ValidationChain: Internal accumulator of validation steps.
    _ValidationResult: Result container with error aggregation.

Type flow:
    validate(value: T) ──> ValidationStartBlock[T]
           |
           └─ assert_that(predicate: Predicate[T])
                 |
                 v
           ValidationAssertBlock[T]
                 |
           ┌─────┴──────────────┐
           |                    |
      assert_that(P[T])     otherwise(P[T])
           |
           v
    ValidationAssertBlock[T]  (T preserved as long as value doesn't change)
           |
           └─ then(new_value: U)
                 |
                 v
      ValidationStartBlock[U]  (new type for the related value)
           |
           └─ assert_that(predicate: Predicate[U])
                 |
                 v
      ValidationAssertBlock[U]  (chain continues, type adapted to U)

Key design decisions:
    - Error aggregation: all steps run, errors collected rather than fail-fast.
    - .otherwise() implements logical OR by combining predicates with _any_of().
    - .then() threads the same _ValidationChain across value changes,
      so chain_validations() and .execute() always see the full picture.
    - _ValidationChain is mutable and shared across blocks in the same chain;
      blocks hold a reference to it, not a copy.
"""

from collections.abc import Callable
from typing import TYPE_CHECKING, Any, final

from ocarina.dsl.invariants.errors import (
    AggregateInvariantViolationError,
    InvariantViolationError,
)

if TYPE_CHECKING:
    from collections.abc import Sequence

type Predicate[T] = Callable[[T], None]


def _with_msg[T](
    predicate: Predicate[T], msg: str | None, name: str | None = None
) -> _PredicateWithMsg[T]:
    """Wrap a predicate with an optional custom error message.

    Args:
        predicate: The validation function to wrap.
        msg: Optional custom error message to use instead of predicate's default.
        name: Optional name prefix for the error message (e.g., "email:").

    Returns:
        A wrapped predicate that uses the custom message on failure.

    """
    prefix = f"{name}:" if name else ""
    full_msg = f"{prefix} {msg}" if msg else None
    return _PredicateWithMsg(predicate, full_msg)


@final
class _PredicateWithMsg[T]:
    """Internal wrapper that associates a predicate with a custom error message.

    This allows predicates to have context-specific error messages while keeping
    the predicate functions themselves reusable.

    Attributes:
        predicate: The validation function.
        msg: Optional custom error message.

    """

    def __init__(self, predicate: Predicate[T], msg: str | None = None) -> None:
        """Initialize the predicate wrapper.

        Args:
            predicate: The validation function to wrap.
            msg: Optional custom error message to override predicate's default.

        """
        self.predicate = predicate
        self.msg = msg

    def __call__(self, value: T) -> None:
        """Execute the predicate with custom error message handling.

        Args:
            value: The value to validate.

        Raises:
            InvariantViolationError: If validation fails.

        """
        try:
            self.predicate(value)
        except InvariantViolationError as exc:
            if self.msg:
                raise InvariantViolationError(self.msg) from exc
            raise


def _any_of[T](*predicates: _PredicateWithMsg[T]) -> _PredicateWithMsg[T]:
    """Create a combined predicate that succeeds if ANY of the predicates succeed.

    This implements logical OR for predicates, used by the .otherwise() method.
    If all predicates fail, an error listing all failures is raised.

    Args:
        *predicates: Variable number of predicates to combine with OR logic.

    Returns:
        A single predicate that passes if at least one input predicate passes.

    Example:
        >>> # age must be exactly 18 OR less than or equal to 65
        >>> combined = _any_of(is_equal_to(18), is_less_than_or_equal_to(65))
        >>> combined(20)  # Passes (satisfies second predicate)
        >>> combined(70)  # Raises (fails both predicates)

    """

    def _try_predicate(
        p: _PredicateWithMsg[T], value: T
    ) -> InvariantViolationError | None:
        try:
            p(value)
        except InvariantViolationError as exc:
            return exc
        else:
            return None

    def combined(value: T) -> None:
        errors = []
        for p in predicates:
            error = _try_predicate(p, value)
            if error is None:
                return
            errors.append(error)

        formatted_error_messages = "  | " + "\n  | ".join(str(e) for e in errors)
        msg = (
            f"All predicates failed for value {value!r}.\n"
            "» At least one of the following conditions must be satisfied:\n"
            f"{formatted_error_messages}"
        )
        raise InvariantViolationError(msg)

    return _PredicateWithMsg(combined)


@final
class _ValidationResult:
    """Container for validation results with error aggregation.

    Attributes:
        is_valid: True if all validations passed, False otherwise.
        errors: List of all InvariantViolationErrors that occurred.
        validated_values: List of values that passed validation.

    """

    def __init__(
        self,
        *,
        is_valid: bool,
        errors: Sequence[InvariantViolationError],
        validated_values: Sequence[Any],
    ) -> None:
        """Initialize validation result.

        Args:
            is_valid: Whether all validations passed.
            errors: Sequence of validation errors (empty if valid).
            validated_values: Sequence of successfully validated values.

        """
        self.is_valid = is_valid
        self.errors = errors
        self.validated_values = validated_values

    def raise_if_invalid(self) -> None:
        """Raise an exception if validation failed.

        Returns:
            None.

        Side Effects:
            Raises an exception if validation failed.

        Raises:
            AggregateInvariantViolationError: If any validations failed,
                containing all accumulated errors.

        Example:
            >>> result = validate(value).assert_that(predicate).execute()
            >>> result.raise_if_invalid()  # Raises if validation failed

        """
        if not self.is_valid:
            raise AggregateInvariantViolationError(self.errors)


@final
class _ValidationChain:
    """Internal accumulator for validation steps.

    This class maintains the list of validation steps and executes them
    sequentially, collecting errors rather than failing fast.

    Attributes:
        _steps: List of (value, name, predicate) tuples to execute.

    """

    def __init__(self) -> None:
        """Initialize an empty validation chain."""
        self._steps: list[tuple[Any, str | None, _PredicateWithMsg[Any]]] = []

    def _merge_chain(self, other: _ValidationChain) -> None:
        """Merge assertions from another chain into this one.

        Args:
            other: Another validation chain whose steps will be appended.

        See Also:
            - chain_validations

        """
        self._steps.extend(other._steps)

    def add_assertion(
        self,
        value: Any,  # noqa: ANN401
        predicate: _PredicateWithMsg[Any],
        name: str | None = None,
    ) -> None:
        """Add a validation step to the chain.

        Args:
            value: The value to validate.
            predicate: The wrapped predicate to apply.
            name: Optional name for better error messages.

        """
        self._steps.append((value, name, predicate))

    def execute(self) -> _ValidationResult:
        """Execute all validation steps and aggregate results.

        Returns:
            A ValidationResult containing success status, errors, and valid values.

        Note:
            This method does NOT raise exceptions. All errors are collected
            and returned in the result. Use result.raise_if_invalid() to raise.

        """

        def run_step(
            value: Any,  # noqa: ANN401
            predicate_with_msg: _PredicateWithMsg[Any],
        ) -> tuple[bool, Any | InvariantViolationError]:
            try:
                predicate_with_msg(value)
            except InvariantViolationError as exc:
                return False, exc
            else:
                return True, value

        errors = []
        validated = []
        for value, _, predicate_with_msg in self._steps:
            success, outcome = run_step(value, predicate_with_msg)
            if success:
                validated.append(outcome)
            else:
                errors.append(outcome)
        return _ValidationResult(
            is_valid=(len(errors) == 0), errors=errors, validated_values=validated
        )


@final
class ValidationStartBlock[T]:
    """Entry point for a validation chain, awaiting the first assertion.

    This is the initial state returned by validate().
    It provides only the assert_that() method to begin validation.

    Type Parameters:
        T: The type of value being validated.

    Example:
        >>> start = validate(42, name="age")
        >>> start.assert_that(is_positive)  # Returns ValidationAssertBlock

    """

    def __init__(
        self, value: T, chain: _ValidationChain | None = None, name: str | None = None
    ) -> None:
        """Initialize a validation start block.

        Args:
            value: The value to validate.
            chain: Optional existing chain to continue (used internally by .then()).
            name: Optional name for this value in error messages.

        """
        self._value = value
        self._chain = chain or _ValidationChain()
        self._name = name

    def assert_that(
        self, predicate: Predicate[T], *, msg: str | None = None
    ) -> ValidationAssertBlock[T]:
        """Add the first validation predicate to the chain.

        Args:
            predicate: A validation function that raises on failure.
            msg: Optional custom error message to use instead of predicate's default.

        Returns:
            A ValidationAssertBlock for further chaining.

        Example:
            >>> validate(email, name="email")
            ...     .assert_that(is_str)
            ...     .assert_that(is_email)

        """
        predicate = _with_msg(predicate, msg, self._name)
        self._chain.add_assertion(self._value, predicate, self._name)
        return ValidationAssertBlock(
            self._value, self._chain, self._name, last_predicate=predicate
        )


@final
class ValidationAssertBlock[T]:
    """Validation block after at least one assertion has been added.

    This block provides multiple options:
    - .assert_that(): Add another validation
    - .otherwise(): Add an alternative predicate (logical OR)
    - .then(): Switch to validating a related value
    - .execute(): Run all validations and get results

    Type Parameters:
        T: The type of value being validated.

    Example:
        >>> validate(age)
        ...     .assert_that(is_positive)
        ...     .assert_that(is_less_than_or_equal_to(120))
        ...     .execute()
        ...     .raise_if_invalid()

    """

    def __init__(
        self,
        value: T,
        chain: _ValidationChain,
        name: str | None = None,
        last_predicate: _PredicateWithMsg[T] | None = None,
    ) -> None:
        """Initialize a validation assert block.

        Args:
            value: The value being validated.
            chain: The validation chain accumulating steps.
            name: Optional name for this value in error messages.
            last_predicate: The most recently added predicate (for .otherwise()).

        """
        self._value = value
        self._chain = chain
        self._name = name
        self._last_predicate = last_predicate
        self._otherwise_predicates: list[_PredicateWithMsg[T]] = []

    def assert_that(
        self, predicate: Predicate[T], msg: str | None = None
    ) -> ValidationAssertBlock[T]:
        """Add another validation predicate (logical AND).

        Args:
            predicate: A validation function that raises on failure.
            msg: Optional custom error message.

        Returns:
            Self for chaining.

        Example:
            >>> validate(password)
            ...     .assert_that(has_min_length(8))
            ...     .assert_that(contains_uppercase)
            ...     .assert_that(contains_digit)

        """
        predicate = _with_msg(predicate, msg, self._name)
        self._chain.add_assertion(self._value, predicate, self._name)
        self._last_predicate = predicate
        self._otherwise_predicates = []
        return self

    def otherwise(
        self, fallback: Predicate[T], *, msg: str | None = None
    ) -> ValidationAssertBlock[T]:
        """Add an alternative predicate.

        Logical OR with the last assertion and any previously added alternatives.

        The validation passes if EITHER the last assert_that() OR this otherwise()
        succeeds. Multiple otherwise() calls create a multi-way OR.

        Args:
            fallback: Alternative validation predicate.
            msg: Optional custom error message for this alternative.

        Returns:
            Self for chaining.

        Example:
            >>> validate(age)
            ...     .assert_that(is_equal_to(18), msg="Must be 18")
            ...     .otherwise(is_equal_to(21), msg="Or must be 21")
            ...     .otherwise(is_equal_to(65), msg="Or must be 65")

        """
        if self._last_predicate is None:  # pragma: no cover
            """Note: Guard to make the type-system happy:
            this case isn't allowed by the fluent API."""

            msg = "otherwise() must follow assert_that()."
            raise RuntimeError(msg)

        fallback_with_msg = _with_msg(fallback, msg, self._name)
        combined = _any_of(
            self._last_predicate, *([*self._otherwise_predicates, fallback_with_msg])
        )
        self._chain._steps.pop()  # noqa: SLF001
        self._chain.add_assertion(self._value, combined, self._name)
        self._last_predicate = combined
        self._otherwise_predicates.append(fallback_with_msg)
        return self

    def then[U](
        self, new_value: U, *, name: str | None = None
    ) -> ValidationStartBlock[U]:
        """Switch to validating a related value, continuing the same chain.

        This allows validating multiple related values in sequence, with all
        errors aggregated together.

        Args:
            new_value: The next value to validate.
            name: Optional name for the new value in error messages.

        Returns:
            A new ValidationStartBlock for the new value.

        Example:
            >>> validate(user, name="user")
            ...     .assert_that(is_not_none)
            ...     .then(user.email, name="email")
            ...     .assert_that(is_email)
            ...     .then(user.age, name="age")
            ...     .assert_that(is_positive)
            ...     .execute()

        """
        return ValidationStartBlock(new_value, self._chain, name)

    def execute(self) -> _ValidationResult:
        """Execute all validation steps and return aggregated results.

        Returns:
            A ValidationResult containing all errors and validated values.

        Note:
            This does NOT raise exceptions. Use .raise_if_invalid() on the
            result to raise an exception if validation failed.

        Example:
            >>> result = validate(x).assert_that(predicate).execute()
            >>> if not result.is_valid:
            ...     logger.error(f"Validation failed: {result.errors}")

        """
        return self._chain.execute()


def chain_validations(
    first: ValidationAssertBlock[Any],
    *rest: ValidationAssertBlock[Any],
) -> ValidationAssertBlock[Any]:
    """Merge multiple independent validation chains into one.

    This allows combining pre-built validation chains, useful for composing
    complex validations from reusable pieces.

    Args:
        first: The first validation chain.
        *rest: Additional validation chains to merge.

    Returns:
        A single ValidationAssertBlock containing all merged validations.

    Example:
        >>> user_validation = validate(user).assert_that(is_not_none)
        >>> email_validation = validate(email).assert_that(is_email)
        >>> combined = chain_validations(user_validation, email_validation)
        >>> combined.execute().raise_if_invalid()

    """
    merged_chain = _ValidationChain()
    merged_chain._merge_chain(first._chain)  # noqa: SLF001

    for block in rest:
        merged_chain._merge_chain(block._chain)  # noqa: SLF001

    return ValidationAssertBlock(first._value, merged_chain, first._name)  # noqa: SLF001
