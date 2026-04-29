"""Helper functions for test results hierarchy."""

from typing import TYPE_CHECKING, Any, TypeGuard

from ocarina.railway.result import Fail, Ok

if TYPE_CHECKING:
    from ocarina.custom_types.oc_test_layers import TestResult


def is_test_result_ok(result: TestResult) -> TypeGuard[Ok[Any]]:
    """Check if test passed, narrowing type to Ok[Any]."""
    return isinstance(result, Ok)


def is_test_result_fail(result: TestResult) -> TypeGuard[Fail]:
    """Check if test failed, narrowing type to Fail."""
    return isinstance(result, Fail)


def is_test_result_skipped(result: TestResult) -> TypeGuard[None]:
    """Check if test was skipped, narrowing type to None."""
    return result is None
