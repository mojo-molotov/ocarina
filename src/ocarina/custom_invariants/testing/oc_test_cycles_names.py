"""Validation of test cycle name: valid cross-platform filename."""

from typing import TYPE_CHECKING

from ocarina.dsl.invariants.assertions import (
    is_valid_filename,
)
from ocarina.dsl.invariants.validate import FrameworkInvariantValidator

if TYPE_CHECKING:
    from ocarina.dsl.invariants.internals.validation_chain import (
        ValidationAssertBlock,
        ValidationStartBlock,
    )


def _test_cycle_name_chain(
    chain: ValidationStartBlock[str],
    _: str,
) -> ValidationAssertBlock[str]:
    msg = "Test cycle name must be valid cross-platform filename."
    return chain.assert_that(is_valid_filename, msg=msg)


def validate_test_cycle_name(
    *, cycle_name: str, name: str
) -> ValidationAssertBlock[str]:
    """Validate that test cycle name is valid cross-platform filename."""
    return FrameworkInvariantValidator.create(cycle_name, name, _test_cycle_name_chain)
