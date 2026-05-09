"""Validation of test runner names: unique and valid cross-platform filenames."""

from typing import TYPE_CHECKING

from ocarina.dsl.invariants.assertions import (
    each,
    has_unique_elements,
    is_valid_filename,
)
from ocarina.dsl.invariants.validate import FrameworkInvariantValidator

if TYPE_CHECKING:
    from collections.abc import Sequence

    from ocarina.dsl.invariants.internals.validation_chain import (
        ValidationAssertBlock,
        ValidationStartBlock,
    )
    from ocarina.dsl.testing.oc_test import Test


def _test_runners_names_chain[Driver](
    chain: ValidationStartBlock[Sequence[Test[Driver]]],
    _: Sequence[Test[Driver]],
) -> ValidationAssertBlock[Sequence[Test[Driver]]]:
    def get_runner_name(t: Test[Driver]) -> str:
        return t.name

    return chain.assert_that(
        has_unique_elements(key=get_runner_name),
        msg="Test runner names must be unique.",
    ).assert_that(
        each(lambda t: is_valid_filename(t.name)),
        msg="Test runner names must be valid cross-platform filenames.",
    )


def validate_test_runners_names[Driver](
    *, tests: Sequence[Test[Driver]], name: str
) -> ValidationAssertBlock[Sequence[Test[Driver]]]:
    """Validate that test runner names are unique and valid cross-platform filenames."""
    return FrameworkInvariantValidator.create(tests, name, _test_runners_names_chain)
