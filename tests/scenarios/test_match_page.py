"""match_page: conditional branching for pages that can render in multiple states."""

# ruff: noqa: S101

import allure
import pytest

from ocarina.custom_errors.test_framework.no_matching_branch import (
    NoMatchingBranchError,
)
from ocarina.dsl.testing_with_railway.match_page import create_match_page, when
from ocarina.opinionated.dsl.drive_page import drive_page
from ocarina.railway.result import is_fail

from .conftest import RecordingPOM, acting

EPIC = "match_page"
FEATURE = "Conditional branching"
LAYER = "unit"
match_page = create_match_page()


@allure.epic(EPIC)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.feature(FEATURE)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.tag("match_page", "happy-path")  # type: ignore[no-untyped-call,untyped-decorator]
@allure.severity(allure.severity_level.CRITICAL)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.label("layer", LAYER)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.title(  # type: ignore[no-untyped-call,untyped-decorator]
    "The first branch whose condition returns True is executed; later branches are skipped"  # noqa: E501
)
def test_first_matching_branch_wins() -> None:  # noqa: D103
    executed: list[str] = []
    pom = RecordingPOM()

    runner = match_page(
        branches=[
            when(
                lambda: False,
                name="first",
                then=[drive_page(acting(pom, "first-branch"))],
            ),
            when(
                lambda: True,
                name="second",
                then=[drive_page(acting(pom, "second-branch"))],
            ),
            when(
                lambda: True,
                name="third",
                then=[drive_page(acting(pom, "third-branch"))],
            ),
        ],
    )

    chain = runner.run()
    executed.extend(pom.calls)

    assert chain.is_ok()
    assert executed == ["second-branch"]


@allure.epic(EPIC)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.feature(FEATURE)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.tag("match_page", "no-match")  # type: ignore[no-untyped-call,untyped-decorator]
@allure.severity(allure.severity_level.NORMAL)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.label("layer", LAYER)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.title("No matching branch produces a NoMatchingBranchError on the failure rail")  # type: ignore[no-untyped-call,untyped-decorator]
def test_no_matching_branch_fails() -> None:  # noqa: D103
    pom = RecordingPOM()

    runner = match_page(
        branches=[
            when(lambda: False, name="a", then=[drive_page(acting(pom, "a"))]),
            when(lambda: False, name="b", then=[drive_page(acting(pom, "b"))]),
        ],
    )

    chain = runner.run()

    assert chain.has_failed()
    result = chain.result()
    assert is_fail(result)
    assert isinstance(result.error, NoMatchingBranchError)
    assert pom.calls == []


@allure.epic(EPIC)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.feature(FEATURE)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.tag("match_page", "error-handling")  # type: ignore[no-untyped-call,untyped-decorator]
@allure.severity(allure.severity_level.NORMAL)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.label("layer", LAYER)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.title("An exception raised by a condition is treated as a non-match by default")  # type: ignore[no-untyped-call,untyped-decorator]
def test_exception_in_condition_is_treated_as_false() -> None:  # noqa: D103
    pom = RecordingPOM()

    def raising_condition() -> bool:
        msg = "condition blew up"
        raise ValueError(msg)

    runner = match_page(
        branches=[
            when(raising_condition, name="raises", then=[drive_page(acting(pom, "r"))]),
            when(lambda: True, name="fallback", then=[drive_page(acting(pom, "f"))]),
        ],
    )

    chain = runner.run()

    assert chain.is_ok()
    assert pom.calls == ["f"]


@allure.epic(EPIC)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.feature(FEATURE)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.tag("match_page", "error-policy")  # type: ignore[no-untyped-call,untyped-decorator]
@allure.severity(allure.severity_level.NORMAL)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.label("layer", LAYER)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.title(  # type: ignore[no-untyped-call,untyped-decorator]
    "Exceptions listed in raised_exceptions propagate instead of being swallowed"
)
def test_raised_exceptions_allowlist_propagates() -> None:  # noqa: D103
    strict_match_page = create_match_page(raised_exceptions=(ValueError,))
    pom = RecordingPOM()

    def raising_condition() -> bool:
        msg = "must propagate"
        raise ValueError(msg)

    runner = strict_match_page(
        branches=[
            when(raising_condition, name="boom", then=[drive_page(acting(pom, "x"))]),
            when(lambda: True, name="fallback", then=[drive_page(acting(pom, "y"))]),
        ],
    )

    with pytest.raises(ValueError, match="must propagate"):
        runner.run()

    assert pom.calls == []
