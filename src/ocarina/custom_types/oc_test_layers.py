"""Type aliases for test results hierarchy.

Defines a hierarchical structure for aggregating test execution results.
Results use Railway Oriented Programming.

Example:
    >>> campaign_results: TestCampaignResults = {
    ...     "test_login": (Ok(None), 5, "test_login"),
    ...     "test_logout": (Fail(error=Exception("Timeout")), 3, "test_logout"),
    ...     "test_optional": (None, 0, "test_optional"),  # Skipped
    ... }

"""

from typing import Any

from ocarina.railway.result import Result

type TestId = str
"""Unique test identifier, typically the test name."""

type _TestStepsCount = int
"""Number of steps executed in a test."""

type TestResult = Result[Any] | None
"""Single test execution result: Ok (passed), Fail (failed), or None (skipped)."""

type TestSuiteResult = tuple[TestResult, _TestStepsCount, TestId]
"""Test result with metadata: (result, steps_count, test_id)."""

type TestSuiteResults = dict[str, TestSuiteResult]
"""Results of all tests in a suite: test_name → TestSuiteResult."""

type TestCampaignResults = dict[str, TestSuiteResults]
"""Results of multiple campaigns: suite_name → TestCampaignResults."""

type TestCycleResults = dict[str, TestCampaignResults]
"""Test cycle results: campaign_name → FullTestSuiteResults."""
