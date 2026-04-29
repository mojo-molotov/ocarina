"""Write-once CLI configuration store with typed field validation.

Provides _CliField[T] — which guarantees validator/value type cohesion when
used directly — and CliStore[TKeys] — which provides key autocompletion only.

Values in CliStore are stored and returned as Any. Python has no mapped types.
There is no value type safety at the CliStore level — the caller is responsible
for casting get() results. If per-field type safety is required, build a typed
facade on top.

_Unset is used as a sentinel to distinguish "not yet set" from any user value,
including None, False, 0, or any other falsy value.

Example:
    >>> from typing import Literal
    >>> from ocarina.dsl import is_positive
    >>> from ocarina.opinionated import CliStore, field
    >>>
    >>> type MyKeys = Literal["workers", "timeout", "headless"]
    >>>
    >>> def create_cli_store() -> CliStore[MyKeys]:
    ...     return CliStore(
    ...         fields={
    ...             "workers": field(validate=lambda chain: chain.assert_that(...)),
    ...             "timeout": field(validate=lambda chain: chain.assert_that(...)),
    ...         }
    ...     )
    >>>
    >>> store = create_cli_store()
    >>> store.set("workers", 4)    # ✅ key autocomplete
    >>> store.set("workers", 4)    # ❌ RuntimeError: already set
    >>> store.get("workers")       # Any — no mapped types in Python
    >>> store.get("unknown")       # ❌ mypy error: not assignable to MyKeys

"""

from typing import Any

from ocarina.dsl.invariants.validate import ValidationChainBuilder
from ocarina.dsl.invariants.validate import validate as _validate


class _Unset:
    """Sentinel type representing an unset field."""


_UNSET = _Unset()


class _CliField[T]:
    """Single write-once CLI field.

    T guarantees that the validator and the stored value share the same type —
    this contract holds when _CliField[T] is used directly.

    Note: When stored in CliStore, T is erased to Any. CliStore provides key
          autocompletion only — not value type safety.

    Uses _Unset as sentinel to distinguish "not set" from any user value,
    including None.
    """

    def __init__(self, *, validate: ValidationChainBuilder[T]) -> None:
        """Initialize the field.

        Args:
            validate: validation chain builder for type T.
                      Receives a ValidationStartBlock[T], returns a built chain.
                      Executed and raised on set().

        """
        self._value: T | _Unset = _UNSET
        self._validate = validate

    def set(self, value: T) -> None:
        """Set the value. Raises if already set or if validation fails.

        Raises:
            RuntimeError: If value has already been set (write-once).
            AggregateInvariantViolationError: If validation chain fails.

        """
        if not isinstance(self._value, _Unset):
            msg = "Value already set."
            raise RuntimeError(msg)  # noqa: TRY004
        self._validate(_validate(value)).execute().raise_if_invalid()
        self._value = value

    def get(self) -> T:
        """Return the stored value. Raises if not yet set.

        Raises:
            RuntimeError: If value has not been set yet.

        """
        if isinstance(self._value, _Unset):
            msg = "Value not set yet."
            raise RuntimeError(msg)  # noqa: TRY004
        return self._value


def field[T](*, validate: ValidationChainBuilder[T]) -> _CliField[T]:
    """Field factory.

    Args:
        validate: validation chain builder. T is inferred from it.

    Example:
        >>> field(validate=lambda chain: chain.assert_that(...))

    """
    return _CliField(validate=validate)


class CliStore[TKeys: str]:
    """Write-once CLI config store with key autocompletion.

    TKeys provides Literal key autocompletion and mypy validation on set()/get().
    Values are stored and returned as Any — Python has no mapped types.

    There is no type safety on values at the CliStore level. set() and get()
    both operate on Any. The caller is responsible for casting get() results.

    If per-field type safety is required, build a typed facade on top.
    """

    def __init__(self, fields: dict[TKeys, _CliField[Any]]) -> None:
        """Initialize the store.

        Args:
            fields: Mapping of Literal keys to _CliField instances.
                    Keys become the valid arguments for set() and get().

        """
        self._fields = fields

    def set(self, k: TKeys, value: Any) -> None:  # noqa: ANN401
        """Set a value by key. Delegates to the underlying _CliField.

        Args:
            k: A valid key (autocompleted from TKeys).
            value: The value to store. Type is checked by _CliField[T] at runtime.

        """
        self._fields[k].set(value)

    def get(self, k: TKeys):
        """Get a value by key. Returns Any — no mapped types in Python.

        Args:
            k: A valid key (autocompleted from TKeys).

        Returns:
            Any: The stored value. Cast to the expected type if needed.

        """
        return self._fields[k].get()
