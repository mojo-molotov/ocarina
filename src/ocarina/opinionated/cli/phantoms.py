"""Phantom for CLI."""

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from ocarina.dsl.invariants.internals.validation_chain import ValidationStartBlock


def _phantom_assertion(_: Any) -> None:  # noqa: ANN401
    """No-op predicate — always passes without any check."""


def phantom_validate(chain: ValidationStartBlock[Any]):
    """Phantom validator — builds a valid chain that always passes.

    Use this for CliStore fields that require a validator but need no actual
    validation — for example, boolean flags set via store_true, or string
    fields whose values are already constrained by argparse choices.

    Args:
        chain: The validation start block to build from.

    Returns:
        A ValidationAssertBlock that always passes.

    Example:
        >>> field(validate=phantom_validate)

    """
    return chain.assert_that(_phantom_assertion)
