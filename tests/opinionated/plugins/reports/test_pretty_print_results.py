"""Tests for pretty_print_results lazy printing behavior."""

# ruff: noqa: S101

from typing import TYPE_CHECKING
from unittest.mock import patch

import allure

from ocarina.opinionated.plugins.reports.pretty_print_results import (
    pretty_print_results,
)
from ocarina.railway.result import Fail, Ok

if TYPE_CHECKING:
    from syrupy.assertion import SnapshotAssertion

    from ocarina.custom_types.oc_test_layers import TestCycleResults, TestSuiteResult

EPIC = "Pretty print"
FEATURE = "Lazy printing"
LAYER = "unit"


def _ok(step: int = 1) -> TestSuiteResult:
    return Ok(None), step, "_name"


def _fail(step: int = 1, error: str = "Something went wrong") -> TestSuiteResult:
    outcome = Fail(Exception(error))
    return outcome, step, "_name"


def _skipped() -> TestSuiteResult:
    return None, -1, "_name"


def _run(results: TestCycleResults, with_colors: bool = False) -> list[str]:  # noqa: FBT001, FBT002
    """Capture stdout lines from pretty_print_results."""
    printed = []
    with patch(
        "builtins.print",
        side_effect=lambda *args: printed.append(args[0] if args else ""),
    ):
        pretty_print_results(results, with_colors=with_colors)
    return printed


@allure.epic(EPIC)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.feature(FEATURE)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.tag("lazy-print", "empty")  # type: ignore[no-untyped-call,untyped-decorator]
@allure.severity(allure.severity_level.CRITICAL)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.label("layer", LAYER)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.title("All suites empty → nothing printed at all")  # type: ignore[no-untyped-call,untyped-decorator]
def test_nothing_printed_when_all_suites_empty(snapshot: SnapshotAssertion) -> None:
    """Campaigns and suites with no tests → nothing printed whatsoever."""
    results: TestCycleResults = {
        "Campaign A": {"Suite 1": {}, "Suite 2": {}},
        "Campaign B": {"Suite 3": {}},
    }
    assert _run(results) == snapshot


@allure.epic(EPIC)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.feature(FEATURE)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.tag("lazy-print", "empty", "suite")  # type: ignore[no-untyped-call,untyped-decorator]
@allure.severity(allure.severity_level.NORMAL)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.label("layer", LAYER)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.title("Empty suite omitted but its parent campaign is still shown")  # type: ignore[no-untyped-call,untyped-decorator]
def test_empty_suite_omitted_but_campaign_shown(snapshot: SnapshotAssertion) -> None:
    """Empty suite is omitted, but the campaign that still has tests is shown."""
    results: TestCycleResults = {
        "Campaign A": {
            "Empty suite": {},
            "Suite with tests": {"Test 1": _ok()},
        }
    }
    assert _run(results) == snapshot


@allure.epic(EPIC)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.feature(FEATURE)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.tag("lazy-print", "empty", "campaign")  # type: ignore[no-untyped-call,untyped-decorator]
@allure.severity(allure.severity_level.NORMAL)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.label("layer", LAYER)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.title("Campaign with all suites empty is fully omitted from output")  # type: ignore[no-untyped-call,untyped-decorator]
def test_empty_campaign_fully_omitted(snapshot: SnapshotAssertion) -> None:
    """Campaign where every suite is empty is not printed at all."""
    results: TestCycleResults = {
        "Empty campaign": {"Suite A": {}, "Suite B": {}},
        "Active campaign": {"Suite C": {"Test 1": _ok()}},
    }
    assert _run(results) == snapshot


@allure.epic(EPIC)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.feature(FEATURE)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.tag("lazy-print", "spacing")  # type: ignore[no-untyped-call,untyped-decorator]
@allure.severity(allure.severity_level.MINOR)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.label("layer", LAYER)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.title("Single active campaign produces no leading blank line")  # type: ignore[no-untyped-call,untyped-decorator]
def test_only_one_active_campaign_no_leading_blank_line(
    snapshot: SnapshotAssertion,
) -> None:
    """Only one active campaign → no leading blank line at the top."""
    results: TestCycleResults = {
        "Empty campaign": {"Suite A": {}},
        "Active campaign": {"Suite B": {"Test 1": _ok()}},
    }
    assert _run(results) == snapshot


@allure.epic(EPIC)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.feature(FEATURE)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.tag("lazy-print", "spacing")  # type: ignore[no-untyped-call,untyped-decorator]
@allure.severity(allure.severity_level.MINOR)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.label("layer", LAYER)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.title("Multiple active campaigns produce a leading blank line")  # type: ignore[no-untyped-call,untyped-decorator]
def test_multiple_active_campaigns_have_leading_blank_line(
    snapshot: SnapshotAssertion,
) -> None:
    """More than one active campaign → leading blank line at the top."""
    results: TestCycleResults = {
        "Campaign A": {"Suite A": {"Test 1": _ok()}},
        "Campaign B": {"Suite B": {"Test 2": _ok()}},
    }
    assert _run(results) == snapshot


@allure.epic(EPIC)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.feature(FEATURE)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.tag("lazy-print", "spacing")  # type: ignore[no-untyped-call,untyped-decorator]
@allure.severity(allure.severity_level.MINOR)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.label("layer", LAYER)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.title(  # type: ignore[no-untyped-call,untyped-decorator]
    "Blank separator appears only between active campaigns, not around empty ones"
)
def test_blank_line_between_active_campaigns_only(snapshot: SnapshotAssertion) -> None:
    """Blank line separates active campaigns only; empty campaigns don't add spacing."""
    results: TestCycleResults = {
        "Campaign A": {"Suite A": {"Test 1": _ok()}},
        "Empty campaign": {"Suite B": {}},
        "Campaign C": {"Suite C": {"Test 2": _ok()}},
    }
    assert _run(results) == snapshot


@allure.epic(EPIC)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.feature(FEATURE)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.tag("lazy-print", "empty", "summary")  # type: ignore[no-untyped-call,untyped-decorator]
@allure.severity(allure.severity_level.NORMAL)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.label("layer", LAYER)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.title("No tests executed → summary block absent from output")  # type: ignore[no-untyped-call,untyped-decorator]
def test_summary_absent_when_no_results(snapshot: SnapshotAssertion) -> None:
    """No tests run → summary block is not printed."""
    results: TestCycleResults = {"Campaign": {"Suite": {}}}
    assert _run(results) == snapshot


@allure.epic(EPIC)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.feature(FEATURE)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.tag("lazy-print", "summary")  # type: ignore[no-untyped-call,untyped-decorator]
@allure.severity(allure.severity_level.NORMAL)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.label("layer", LAYER)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.title("Summary counts only tests from non-empty suites")  # type: ignore[no-untyped-call,untyped-decorator]
def test_summary_counts_only_executed_tests(snapshot: SnapshotAssertion) -> None:
    """Counters reflect only tests that actually ran; empty suites are excluded."""
    results: TestCycleResults = {
        "Campaign": {
            "Empty suite": {},
            "Active suite": {
                "T1": _ok(),
                "T2": _fail(),
                "T3": _skipped(),
            },
        }
    }
    assert _run(results) == snapshot
