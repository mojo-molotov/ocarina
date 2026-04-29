"""Tests for generate_json_results lazy writing behavior."""

# ruff: noqa: S101

import json
from typing import TYPE_CHECKING, Any
from unittest.mock import MagicMock, patch

import allure

from ocarina.opinionated.plugins.reports.results_to_json import generate_json_results
from ocarina.railway.result import Fail, Ok

if TYPE_CHECKING:
    from pathlib import Path

    from syrupy.assertion import SnapshotAssertion

    from ocarina.custom_types.oc_test_layers import TestCycleResults, TestSuiteResult

EPIC = "JSON results"
FEATURE = "Lazy writing"
LAYER = "unit"

FIXED_UUID = "abcd1234efgh5678"
FIXED_FILENAME = f"{FIXED_UUID[:8]}.json"


def _ok(step: int = 1) -> TestSuiteResult:
    return Ok(None), step, "_name"


def _fail(step: int = 1, error: str = "Something went wrong") -> TestSuiteResult:
    outcome = Fail(Exception(error))
    return outcome, step, "_name"


def _skipped() -> TestSuiteResult:
    return None, -1, "_name"


def _run(
    results: TestCycleResults,
    tmp_path: Path,
) -> tuple[dict[str, dict[str, dict[str, Any]]], MagicMock]:
    """Run generate_json_results with a fixed UUID and a recording logger."""
    logger = MagicMock()
    mock_uuid = MagicMock()
    mock_uuid.hex = FIXED_UUID

    with patch(
        "ocarina.opinionated.plugins.reports.results_to_json.uuid.uuid4",
        return_value=mock_uuid,
    ):
        generate_json_results(results=results, output_dir=tmp_path, logger=logger)

    file_path = tmp_path / FIXED_FILENAME
    payload = (
        json.loads(file_path.read_text(encoding="utf-8")) if file_path.exists() else {}
    )
    return payload, logger


@allure.epic(EPIC)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.feature(FEATURE)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.tag("lazy-write", "empty")  # type: ignore[no-untyped-call,untyped-decorator]
@allure.severity(allure.severity_level.CRITICAL)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.label("layer", LAYER)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.title("All suites empty → no file written, warning logged")  # type: ignore[no-untyped-call,untyped-decorator]
def test_nothing_written_when_all_suites_empty(
    tmp_path: Path, snapshot: SnapshotAssertion
) -> None:
    """All campaigns and suites empty → no JSON file created, warning issued."""
    results: TestCycleResults = {
        "Campaign A": {"Suite 1": {}, "Suite 2": {}},
        "Campaign B": {"Suite 3": {}},
    }
    _, logger = _run(results, tmp_path)

    assert not (tmp_path / FIXED_FILENAME).exists()
    assert logger.warning.call_args_list == snapshot


@allure.epic(EPIC)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.feature(FEATURE)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.tag("lazy-write", "empty", "suite")  # type: ignore[no-untyped-call,untyped-decorator]
@allure.severity(allure.severity_level.NORMAL)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.label("layer", LAYER)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.title("Empty suite omitted from JSON but parent campaign is present")  # type: ignore[no-untyped-call,untyped-decorator]
def test_empty_suite_omitted_but_campaign_written(
    tmp_path: Path, snapshot: SnapshotAssertion
) -> None:
    """Empty suite is stripped from the payload; the campaign still appears."""
    results: TestCycleResults = {
        "Campaign A": {
            "Empty suite": {},
            "Suite with tests": {"Test 1": _ok()},
        }
    }
    payload, _ = _run(results, tmp_path)
    assert payload == snapshot


@allure.epic(EPIC)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.feature(FEATURE)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.tag("lazy-write", "empty", "campaign")  # type: ignore[no-untyped-call,untyped-decorator]
@allure.severity(allure.severity_level.NORMAL)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.label("layer", LAYER)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.title("Campaign with all suites empty is fully omitted from JSON")  # type: ignore[no-untyped-call,untyped-decorator]
def test_empty_campaign_fully_omitted(
    tmp_path: Path, snapshot: SnapshotAssertion
) -> None:
    """Campaign where every suite is empty does not appear in the JSON payload."""
    results: TestCycleResults = {
        "Empty campaign": {"Suite A": {}, "Suite B": {}},
        "Active campaign": {"Suite C": {"Test 1": _ok()}},
    }
    payload, _ = _run(results, tmp_path)
    assert payload == snapshot


@allure.epic(EPIC)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.feature(FEATURE)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.tag("lazy-write", "happy-path")  # type: ignore[no-untyped-call,untyped-decorator]
@allure.severity(allure.severity_level.CRITICAL)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.label("layer", LAYER)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.title("Full results with all outcome types serialize correctly")  # type: ignore[no-untyped-call,untyped-decorator]
def test_full_results_serialize_correctly(
    tmp_path: Path, snapshot: SnapshotAssertion
) -> None:
    """Ok, Fail, and skipped outcomes all serialize to the expected JSON structure."""
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
    payload, _ = _run(results, tmp_path)
    assert payload == snapshot
