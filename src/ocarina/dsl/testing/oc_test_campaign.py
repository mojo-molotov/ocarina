"""Campaigns: orchestrates multiple TestSuites instances with shared config.

Test hierarchy:
    TestCycle → Campaigns → TestSuites → Tests
"""

from typing import TYPE_CHECKING

from ocarina.aggregates.tests_layers import is_test_result_fail
from ocarina.custom_invariants.testing.oc_test_suites_names import (
    validate_test_suites_names,
)

if TYPE_CHECKING:
    from collections.abc import Sequence

    from ocarina.custom_types.oc_test_layers import TestCampaignResults
    from ocarina.dsl.testing.oc_test_suite import TestSuite


class TestCampaign[Driver]:
    """Orchestrator for a sequence of related suites with shared worker config.

    Campaigns run sequentially; tests within each suite run in parallel.
    Injects campaign name into each suite for logging taxonomy.
    """

    def __init__(
        self,
        *,
        name: str,
        suites: Sequence[TestSuite[Driver]],
        max_workers: int,
        saturate_workers: bool | None = None,
    ) -> None:
        """Initialize the sequence.

        Args:
            name: Campaign name used in logs and reports.
            suites: Suites to execute. Must have unique names.
            max_workers: Concurrent workers applied to all campaigns.
            saturate_workers: Duplicate tests to reach max_workers. Default: None.

        Raises:
            AggregateInvariantViolationError: If suite names are not unique.

        """
        validate_test_suites_names(
            suites=suites, name="suites"
        ).execute().raise_if_invalid()

        self.name = name
        self._suites = suites
        self._results: TestCampaignResults = {}
        self._max_workers = max_workers
        self._saturate_workers = saturate_workers

        for suite in self._suites:
            suite._campaign_name = self.name  # noqa: SLF001

    def run_all(
        self, *, skip_all: bool = False, saturate_workers: bool = True
    ) -> TestCampaignResults:
        """Execute all suites sequentially.

        Args:
            skip_all: If True, mark all tests as skipped without executing.
            saturate_workers: Duplicate tests to reach max_workers. Default: True.

        Returns:
            Dict mapping suite name → campaign results.

        """
        self._results.clear()

        resolved_saturate_workers = (
            self._saturate_workers
            if self._saturate_workers is not None
            else saturate_workers
        )

        if skip_all:
            for suite in self._suites:
                self._results[suite.name] = {
                    name: (None, -1, test_id)
                    for name, test_id in suite.test_names_and_ids
                }
            return self._results

        for suite in self._suites:
            self._results[suite.name] = suite.run(
                max_workers=self._max_workers,
                saturate_workers=resolved_saturate_workers,
            )

        return self._results


def campaign_has_failed(results: TestCampaignResults) -> bool:
    """Return True if any test in the campaign results has a Fail outcome.

    Skipped (None) and passed (Ok) tests return False.
    """
    return any(
        is_test_result_fail(outcome)
        for campaign_results in results.values()
        for outcome, _, _ in campaign_results.values()
    )
