"""Validation of test runner names: must be unique."""

from typing import TYPE_CHECKING

from ocarina.dsl.invariants.assertions import has_unique_elements
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
    )


def validate_test_runners_names[Driver](
    *, tests: Sequence[Test[Driver]], name: str
) -> ValidationAssertBlock[Sequence[Test[Driver]]]:
    """Validate that all test runner names are unique."""
    return FrameworkInvariantValidator.create(tests, name, _test_runners_names_chain)
