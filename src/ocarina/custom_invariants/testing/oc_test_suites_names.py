"""Validation of test suite names: must be unique."""

from typing import TYPE_CHECKING

from ocarina.dsl.invariants.assertions import has_unique_elements
from ocarina.dsl.invariants.validate import FrameworkInvariantValidator

if TYPE_CHECKING:
    from collections.abc import Sequence

    from ocarina.dsl.invariants.internals.validation_chain import (
        ValidationAssertBlock,
        ValidationStartBlock,
    )
    from ocarina.dsl.testing.oc_test_suite import TestSuite


def _test_suites_names_chain[Driver](
    chain: ValidationStartBlock[Sequence[TestSuite[Driver]]],
    _: Sequence[TestSuite[Driver]],
) -> ValidationAssertBlock[Sequence[TestSuite[Driver]]]:
    def get_suite_name(c: TestSuite[Driver]) -> str:
        return c.name

    return chain.assert_that(
        has_unique_elements(key=get_suite_name),
        msg="Test suite names must be unique.",
    )


def validate_test_suites_names[Driver](
    *, suites: Sequence[TestSuite[Driver]], name: str
) -> ValidationAssertBlock[Sequence[TestSuite[Driver]]]:
    """Validate that all test suite names are unique."""
    return FrameworkInvariantValidator.create(suites, name, _test_suites_names_chain)
