"""Full test suite orchestrator.

Hierarchy: TestCycle → Campaigns → TestSuites → Tests

Smoke tests run first. If any fail, main campaigns sequences are skipped.
Execution modes control whether smoke sequences stop on first failure or all run.
"""

from typing import TYPE_CHECKING, Literal, final

from ocarina.aggregates.tests_layers import is_test_result_fail
from ocarina.custom_invariants.testing.oc_test_campaigns_names import (
    validate_campaigns_names,
)
from ocarina.custom_invariants.testing.oc_test_cycles_names import (
    validate_test_cycle_name,
)
from ocarina.dsl.invariants.internals.validation_chain import chain_validations
from ocarina.dsl.testing.oc_test_campaign import (
    TestCampaign,
    campaign_has_failed,
)

if TYPE_CHECKING:
    from collections.abc import Sequence

    from ocarina.custom_types.oc_test_layers import TestCycleResults
    from ocarina.custom_types.thunk import Thunk

type Mode = Literal[
    "fail-fast-on-first-smoke-campaigns-sequence-fail",
    "wait-for-all-smoke-tests",
]
"""Smoke test failure handling mode.

- fail-fast: Stop smoke sequences on first failure, skip all remaining.
- wait-for-all: Run all smoke sequences, skip main tests if any failed.
"""


@final
class TestCycle[Driver]:
    """Top-level orchestrator for smoke + main test campaigns sequences.

    Smoke sequences run first. Main sequences are skipped if any smoke test failed.
    Sequence names must be unique across smoke and main sequences.
    """

    def __init__(
        self,
        *,
        name: str,
        campaigns: Sequence[TestCampaign[Driver]],
        smoke_tests_campaigns: Sequence[TestCampaign[Driver]] | None = None,
        mode: Mode | None = None,
    ) -> None:
        """Initialize test suite.

        Args:
            name: Cycle name used in logs and reports.
            campaigns: Main campaigns, run after smoke tests.
            smoke_tests_campaigns: Smoke campaigns, run first. Default: none.
            mode: Failure handling mode. Default: fail-fast.

        Raises:
            AggregateInvariantViolationError: If campaign names are not unique.

        """
        if mode is None:
            mode = "fail-fast-on-first-smoke-campaigns-sequence-fail"

        smoke_campaigns = smoke_tests_campaigns or []

        chain_validations(
            validate_test_cycle_name(cycle_name=name, name="test_cycle"),
            validate_campaigns_names(
                campaigns=[*smoke_campaigns, *campaigns],
                name="all campaigns (smoke + deep tests)",
            ),
        ).execute().raise_if_invalid()

        self.name = name
        self._campaigns = campaigns
        self._smoke_campaigns = smoke_campaigns
        self._results: TestCycleResults = {}
        self._mode = mode

        for campaign in self._campaigns:
            for suite in campaign._suites:  # noqa: SLF001
                suite._cycle_name = name  # noqa: SLF001

        for smoke_campaign in self._smoke_campaigns:
            for suite in smoke_campaign._suites:  # noqa: SLF001
                suite._cycle_name = name  # noqa: SLF001

    def run_all(self, *, saturate_workers: bool = True) -> TestCycleResults:
        """Run smoke sequences then main sequences. Returns aggregated results.

        Main sequences are skipped if any smoke test failed.
        Smoke behavior depends on configured mode.

        Args:
            saturate_workers: Duplicate tests to reach max_workers. Default: True.

        """
        self._results.clear()

        def _run_smoke(*, fail_fast: bool) -> bool:
            failed = False
            for campaign in self._smoke_campaigns:
                results = campaign.run_all(
                    skip_all=failed if fail_fast else False,
                    saturate_workers=saturate_workers,
                )
                self._results[campaign.name] = results
                if campaign_has_failed(results):
                    failed = True
            return failed

        dispatch: dict[Mode, Thunk[bool]] = {
            "fail-fast-on-first-smoke-campaigns-sequence-fail": lambda: _run_smoke(
                fail_fast=True
            ),
            "wait-for-all-smoke-tests": lambda: _run_smoke(fail_fast=False),
        }

        skip_all = dispatch[self._mode]()

        for campaign in self._campaigns:
            self._results[campaign.name] = campaign.run_all(
                skip_all=skip_all, saturate_workers=saturate_workers
            )

        return self._results


def has_test_cycle_failed(results: TestCycleResults) -> bool:
    """Is true if any test failed."""
    return any(
        is_test_result_fail(outcome)
        for campaigns in results.values()
        for tests in campaigns.values()
        for outcome, _, _ in tests.values()
    )
