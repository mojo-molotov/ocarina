"""Railway and action-chain behavior.

Covers the smallest primitive users touch: create_act, drive_page, and the
Ok/Fail discrimination underneath. Every assertion checks an outcome a user
would actually care about, never an internal attribute.
"""

# ruff: noqa: S101

import allure

from ocarina.dsl.testing_with_railway.constructors.create_act import create_act
from ocarina.opinionated.dsl.drive_page import drive_page
from ocarina.opinionated.infra.act_counter import ActCounter
from ocarina.railway.result import Fail, Ok, is_fail, is_ok

from .conftest import RecordingPOM, acting

EPIC = "Railway / action chain"
FEATURE = "Action chain"
LAYER = "unit"


@allure.epic(EPIC)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.feature(FEATURE)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.tag("railway", "result")  # type: ignore[no-untyped-call,untyped-decorator]
@allure.severity(allure.severity_level.NORMAL)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.label("layer", LAYER)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.title("is_ok and is_fail discriminate Ok from Fail")  # type: ignore[no-untyped-call,untyped-decorator]
def test_result_discriminators_split_ok_and_fail() -> None:  # noqa: D103
    ok: Ok[int] = Ok(value=42)
    fail = Fail(error=RuntimeError("x"))

    assert is_ok(ok)
    assert not is_fail(ok)
    assert is_fail(fail)
    assert not is_ok(fail)


@allure.epic(EPIC)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.feature(FEATURE)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.tag("act", "handlers", "happy-path")  # type: ignore[no-untyped-call,untyped-decorator]
@allure.severity(allure.severity_level.CRITICAL)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.label("layer", LAYER)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.title("A successful act reports success; the success handler fires once")  # type: ignore[no-untyped-call,untyped-decorator]
def test_success_act_fires_success_handler() -> None:  # noqa: D103
    pom = RecordingPOM()
    calls = {"success": 0, "failure": 0}

    chain = (
        create_act(pom, lambda p: p.step("click"))
        .failure(lambda _: calls.__setitem__("failure", calls["failure"] + 1))
        .success(lambda: calls.__setitem__("success", calls["success"] + 1))
        .execute()
    )

    assert chain.is_ok()
    assert pom.calls == ["click"]
    assert calls == {"success": 1, "failure": 0}


@allure.epic(EPIC)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.feature(FEATURE)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.tag("act", "error-handling")  # type: ignore[no-untyped-call,untyped-decorator]
@allure.severity(allure.severity_level.CRITICAL)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.label("layer", LAYER)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.title(  # type: ignore[no-untyped-call,untyped-decorator]
    "A raising action is caught into Fail; the failure handler fires with the exception"
)
def test_raising_act_is_captured_as_fail() -> None:  # noqa: D103
    pom = RecordingPOM(raise_on={"boom"}, raises_with={"boom": ValueError("nope")})
    captured: list[Exception] = []

    chain = (
        create_act(pom, lambda p: p.step("boom"))
        .failure(captured.append)
        .success(lambda: None)
        .execute()
    )

    assert chain.has_failed()
    assert len(captured) == 1
    assert isinstance(captured[0], ValueError)
    assert str(captured[0]) == "nope"


@allure.epic(EPIC)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.feature(FEATURE)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.tag("act", "error-handling", "hook")  # type: ignore[no-untyped-call,untyped-decorator]
@allure.severity(allure.severity_level.NORMAL)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.label("layer", LAYER)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.title("on_failure hook can translate exceptions into a custom Fail")  # type: ignore[no-untyped-call,untyped-decorator]
def test_on_failure_hook_translates_exception() -> None:  # noqa: D103
    class CustomError(Exception): ...

    pom = RecordingPOM(raise_on={"boom"})

    def translate(_pom: RecordingPOM, exc: Exception) -> Fail:
        return Fail(error=CustomError(f"translated: {exc}"))

    chain = (
        create_act(pom, lambda p: p.step("boom"), on_failure=translate)
        .failure(lambda _: None)
        .success(lambda: None)
        .execute()
    )

    result = chain.result()
    assert is_fail(result)  # type: ignore[arg-type]
    assert isinstance(result.error, CustomError)
    assert "translated: boom failed" in str(result.error)


@allure.epic(EPIC)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.feature(FEATURE)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.tag("drive_page", "short-circuit")  # type: ignore[no-untyped-call,untyped-decorator]
@allure.severity(allure.severity_level.CRITICAL)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.label("layer", LAYER)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.title("drive_page short-circuits: steps after a failure are never executed")  # type: ignore[no-untyped-call,untyped-decorator]
def test_drive_page_short_circuits_after_failure() -> None:  # noqa: D103
    pom = RecordingPOM(raise_on={"b"})

    chain = drive_page(
        acting(pom, "a"),
        acting(pom, "b"),
        acting(pom, "c"),
    ).run()

    assert chain.has_failed()
    assert pom.calls == ["a", "b"]  # 'c' never ran


@allure.epic(EPIC)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.feature(FEATURE)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.tag("drive_page", "happy-path")  # type: ignore[no-untyped-call,untyped-decorator]
@allure.severity(allure.severity_level.CRITICAL)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.label("layer", LAYER)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.title("drive_page runs all steps to completion on the happy path")  # type: ignore[no-untyped-call,untyped-decorator]
def test_drive_page_runs_all_on_success() -> None:  # noqa: D103
    pom = RecordingPOM()

    chain = drive_page(
        acting(pom, "a"),
        acting(pom, "b"),
        acting(pom, "c"),
    ).run()

    assert chain.is_ok()
    assert pom.calls == ["a", "b", "c"]


@allure.epic(EPIC)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.feature(FEATURE)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.tag("act_counter")  # type: ignore[no-untyped-call,untyped-decorator]
@allure.severity(allure.severity_level.MINOR)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.label("layer", LAYER)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.title(  # type: ignore[no-untyped-call,untyped-decorator]
    "The act counter increments once per executed act and is isolated to the current thread"  # noqa: E501
)
def test_act_counter_increments_per_act() -> None:  # noqa: D103
    counter = ActCounter()
    counter.reset()
    pom = RecordingPOM()

    drive_page(
        acting(pom, "a"),
        acting(pom, "b"),
        acting(pom, "c"),
    ).run()

    assert counter.get() == 3  # noqa: PLR2004
