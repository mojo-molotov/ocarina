"""Validation of test suite names: unique and valid cross-platform filenames."""

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
    from ocarina.dsl.testing.oc_test_suite import TestSuite


def _test_suites_names_chain[Driver](
    chain: ValidationStartBlock[Sequence[TestSuite[Driver]]],
    _: Sequence[TestSuite[Driver]],
) -> ValidationAssertBlock[Sequence[TestSuite[Driver]]]:
    def get_suite_name(s: TestSuite[Driver]) -> str:
        return s.name

    return chain.assert_that(
        has_unique_elements(key=get_suite_name),
        msg="Test suite names must be unique.",
    ).assert_that(
        each(lambda s: is_valid_filename(s.name)),
        msg="Test suites names must be valid cross-platform filenames.",
    )


def validate_test_suites_names[Driver](
    *, suites: Sequence[TestSuite[Driver]], name: str
) -> ValidationAssertBlock[Sequence[TestSuite[Driver]]]:
    """Validate that test suite names are unique and valid cross-platform filenames."""
    return FrameworkInvariantValidator.create(suites, name, _test_suites_names_chain)
