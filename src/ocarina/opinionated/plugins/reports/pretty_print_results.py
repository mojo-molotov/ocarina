# ruff: noqa: T201
"""Displays the full test results.

This module provides a pretty printer to display, in a structured and readable
way, the results of a complete test suite. It supports hierarchical display
(campaigns > suites > cases) with optional colorization.

Architecture:
    - Recursive traversal of the results structure
    - Dispatch pattern to map outcomes → textual statuses
    - Conditional colorization via ANSI codes
    - Statistics accumulation for final summary

Output format:
    Campaign
    • Suite
      > Test case 1
        » PASSED
      > Test case 2
        » FAILED
          → Error message
            ⫸ At step 3
      > Test case 3
        » SKIPPED

    Test results:
    1 FAILED | 1 PASSED | 1 SKIPPED

Features:
    - ANSI color support (green/red)
    - Error message display with context (step number)
    - Smart spacing between groups

Typical usage:
    >>> results = run_all_tests()
    >>> pretty_print_results(results, with_colors=True)

"""

from typing import TYPE_CHECKING, Final

from ocarina.aggregates.tests_layers import (
    is_test_result_fail,
    is_test_result_ok,
    is_test_result_skipped,
)
from ocarina.railway.result import Fail, Ok

if TYPE_CHECKING:
    from ocarina.custom_types.oc_test_layers import (
        TestCycleResults,
    )

_FAIL: Final[str] = "FAILED"
_SUCCESS: Final[str] = "PASSED"
_SKIPPED: Final[str] = "SKIPPED"
_FINAL_SUMUP_HEADLINE: Final[str] = "Test results:"

_STATUS_DISPATCH = {
    Fail: _FAIL,
    Ok: _SUCCESS,
    type(None): _SKIPPED,
}

_GREEN = "\033[32m"
_RED = "\033[31m"
_COLOR_RESET = "\033[0m"


def _color_text(text: str, color_code: str) -> str:
    return f"{color_code}{text}{_COLOR_RESET}"


def _muted_color_text(text: str, color_code: str) -> str:  # noqa: ARG001
    return text


def _upcase(word: str) -> str:
    return word.upper()


def pretty_print_results(  # noqa: PLR0912
    results: TestCycleResults, *, with_colors: bool = False
) -> None:
    """Pretty printer."""
    _color = _color_text if with_colors else _muted_color_text

    count_ok = 0
    count_fail = 0
    count_ignored = 0

    campaigns_output: list[list[str]] = []

    for campaign_name, campaigns in results.items():
        campaign_lines: list[str] = []

        for suite_name, tests in campaigns.items():
            if not tests:
                continue

            suite_lines: list[str] = [f"• {suite_name}"]

            for test_name, (outcome, counter, _) in tests.items():
                status = _STATUS_DISPATCH.get(type(outcome), "???")
                suite_lines.append(f"  › {test_name}")  # noqa: RUF001

                if is_test_result_fail(outcome):
                    count_fail += 1
                    suite_lines.append(_color(f"    » {status}", _RED))
                    error_msg = str(outcome.error).rstrip("\n") if outcome.error else ""
                    if error_msg:
                        suite_lines.append(_color(f"      → {error_msg}", _RED))
                        suite_lines.append(_color(f"        ⫸ At step {counter}", _RED))
                    else:
                        suite_lines.append(_color(f"      → At step {counter}", _RED))
                elif is_test_result_ok(outcome):
                    count_ok += 1
                    suite_lines.append(_color(f"    » {status}", _GREEN))
                elif is_test_result_skipped(outcome):
                    count_ignored += 1
                    suite_lines.append(f"    » {status}")
                else:
                    suite_lines.append(f"    » {status}")

            campaign_lines.extend(suite_lines)

        if campaign_lines:
            campaigns_output.append([campaign_name, *campaign_lines])

    if len(campaigns_output) > 1:
        print()

    for i, campaign_lines in enumerate(campaigns_output):
        for line in campaign_lines:
            print(line)
        if i < len(campaigns_output) - 1:
            print()

    summary_parts = []
    if count_fail > 0:
        summary_parts.append(_color(f"{count_fail} {_upcase(_FAIL)}", _RED))
    if count_ok > 0:
        summary_parts.append(_color(f"{count_ok} {_upcase(_SUCCESS)}", _GREEN))
    if count_ignored > 0:
        summary_parts.append(f"{count_ignored} {_upcase(_SKIPPED)}")

    if summary_parts:
        print()
        print(_FINAL_SUMUP_HEADLINE)
        print(" | ".join(summary_parts))
