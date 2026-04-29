"""Validation of test runner IDs: must be unique."""

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


def _test_runners_ids_chain[Driver](
    chain: ValidationStartBlock[Sequence[Test[Driver]]],
    _: Sequence[Test[Driver]],
) -> ValidationAssertBlock[Sequence[Test[Driver]]]:
    def get_runner_id(t: Test[Driver]) -> str:
        return t.test_id

    return chain.assert_that(
        has_unique_elements(key=get_runner_id),
        msg="Test runner IDs must be unique.",
    )


def validate_test_runners_ids[Driver](
    *, tests: Sequence[Test[Driver]], name: str
) -> ValidationAssertBlock[Sequence[Test[Driver]]]:
    """Validate that all test runner IDs are unique."""
    return FrameworkInvariantValidator.create(tests, name, _test_runners_ids_chain)
