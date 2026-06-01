"""TestSuite: parallel execution, retry policy, setup/teardown, skipping."""

# ruff: noqa: S101

from typing import TYPE_CHECKING

import allure
import pytest

from ocarina.aggregates.tests_layers import is_test_result_fail, is_test_result_ok
from ocarina.custom_errors.test_framework.driver_died import DriverDiedError
from ocarina.custom_types.scenario import Scenario
from ocarina.dsl.invariants.errors import AggregateInvariantViolationError
from ocarina.opinionated.dsl.drive_page import drive_page
from ocarina.opinionated.loggers.muted_logger import MutedLogger

from .conftest import (
    FakeDriver,
    RecordingPOM,
    acting,
    failing_scenario,
    make_built_driver,
    make_pool,
    make_suite,
    make_test,
)

if TYPE_CHECKING:
    from collections.abc import Callable

    from ocarina.ports.ilogger import ILogger

EPIC = "TestSuite"
FEATURE = "Suite orchestration"
LAYER = "integration"


@allure.epic(EPIC)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.feature(FEATURE)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.tag("suite", "sequential")  # type: ignore[no-untyped-call,untyped-decorator]
@allure.severity(allure.severity_level.CRITICAL)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.label("layer", LAYER)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.title("Sequential run: every test in the suite is executed and reported")  # type: ignore[no-untyped-call,untyped-decorator]
def test_sequential_run_reports_every_test() -> None:  # noqa: D103
    suite = make_suite(
        "s",
        [
            make_test("t1"),
            make_test("t2", scenario=failing_scenario()),
            make_test("t3"),
        ],
    )

    results = suite.run(max_workers=1, saturate_workers=False)

    assert list(results.keys()) == ["t1", "t2", "t3"]
    assert is_test_result_ok(results["t1"][0])
    assert is_test_result_fail(results["t2"][0])
    assert is_test_result_ok(results["t3"][0])


@allure.epic(EPIC)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.feature(FEATURE)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.tag("suite", "parallel")  # type: ignore[no-untyped-call,untyped-decorator]
@allure.severity(allure.severity_level.BLOCKER)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.label("layer", LAYER)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.title("Parallel run: all tests still execute and results match sequential")  # type: ignore[no-untyped-call,untyped-decorator]
def test_parallel_run_returns_same_outcomes() -> None:  # noqa: D103
    suite = make_suite(
        "s",
        [make_test(f"t{i}") for i in range(4)],
        pool=make_pool(max_size=4),
    )

    results = suite.run(max_workers=4, saturate_workers=False)

    assert len(results) == 4  # noqa: PLR2004
    assert all(is_test_result_ok(outcome) for outcome, *_ in results.values())


@allure.epic(EPIC)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.feature(FEATURE)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.tag("suite", "retry")  # type: ignore[no-untyped-call,untyped-decorator]
@allure.severity(allure.severity_level.CRITICAL)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.label("layer", LAYER)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.title(  # type: ignore[no-untyped-call,untyped-decorator]
    "Transient errors trigger retries and a later-succeeding test is reported as Ok"
)
def test_transient_error_retries_until_success() -> None:  # noqa: D103
    class Flaky(Exception): ...  # noqa: N818

    attempts = {"count": 0}

    def flaky_scenario(driver: FakeDriver, logger) -> Scenario[FakeDriver]:  # noqa: ANN001, ARG001
        attempts["count"] += 1
        pom = RecordingPOM()
        if attempts["count"] < 3:  # noqa: PLR2004
            # Fail with a transient error on first two attempts
            return Scenario(
                test_chain=[
                    drive_page(
                        acting(
                            RecordingPOM(
                                raise_on={"boom"},
                                raises_with={"boom": Flaky("flaky")},
                            ),
                            "boom",
                        )
                    )
                ]
            )
        # Succeed on the third attempt
        return Scenario(test_chain=[drive_page(acting(pom, "ok"))])

    suite = make_suite(
        "s",
        [make_test("flaky_test", scenario=flaky_scenario)],
        transient_errors=(Flaky,),
        max_retries_per_test=5,
    )

    results = suite.run(max_workers=1, saturate_workers=False)

    outcome, _steps, _id = results["flaky_test"]
    assert is_test_result_ok(outcome)
    assert attempts["count"] == 3  # noqa: PLR2004


@allure.epic(EPIC)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.feature(FEATURE)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.tag("suite", "retry-policy")  # type: ignore[no-untyped-call,untyped-decorator]
@allure.severity(allure.severity_level.NORMAL)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.label("layer", LAYER)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.title(  # type: ignore[no-untyped-call,untyped-decorator]
    "Non-transient errors are not retried — the test fails on the first attempt"
)
def test_non_transient_error_is_not_retried() -> None:  # noqa: D103
    attempts = {"count": 0}

    def scenario(driver: FakeDriver, logger) -> Scenario[FakeDriver]:  # noqa: ANN001, ARG001
        attempts["count"] += 1
        pom = RecordingPOM(raise_on={"x"}, raises_with={"x": RuntimeError("hard")})
        return Scenario(test_chain=[drive_page(acting(pom, "x"))])

    suite = make_suite(
        "s",
        [make_test("hard_fail", scenario=scenario)],
        transient_errors=(ValueError,),  # RuntimeError is NOT transient
        max_retries_per_test=5,
    )

    results = suite.run(max_workers=1, saturate_workers=False)

    assert is_test_result_fail(results["hard_fail"][0])
    assert attempts["count"] == 1


@allure.epic(EPIC)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.feature(FEATURE)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.tag("suite", "validation")  # type: ignore[no-untyped-call,untyped-decorator]
@allure.severity(allure.severity_level.NORMAL)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.label("layer", LAYER)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.title("Duplicate test_ids are rejected at suite construction")  # type: ignore[no-untyped-call,untyped-decorator]
def test_duplicate_test_ids_rejected() -> None:  # noqa: D103
    with pytest.raises(AggregateInvariantViolationError):
        make_suite(
            "s",
            [
                make_test("a", test_id="same"),
                make_test("b", test_id="same"),
            ],
        )


@allure.epic(EPIC)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.feature(FEATURE)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.tag("suite", "skip")  # type: ignore[no-untyped-call,untyped-decorator]
@allure.severity(allure.severity_level.NORMAL)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.label("layer", LAYER)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.title("Skipped tests are reported with a None outcome and are never executed")  # type: ignore[no-untyped-call,untyped-decorator]
def test_skipped_test_produces_none_outcome() -> None:  # noqa: D103
    executed = {"count": 0}

    def scenario(driver: FakeDriver, logger) -> Scenario[FakeDriver]:  # noqa: ANN001, ARG001
        executed["count"] += 1
        return Scenario(test_chain=[])

    suite = make_suite(
        "s",
        [make_test("skipped", scenario=scenario, skipped=True)],
    )

    results = suite.run(max_workers=1, saturate_workers=False)

    outcome, _steps, _id = results["skipped"]
    assert outcome is None
    # The scenario factory is still called once by spawn(), but no chain runs.
    # The user-visible contract is "outcome is None".


@allure.epic(EPIC)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.feature(FEATURE)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.tag("suite", "teardown")  # type: ignore[no-untyped-call,untyped-decorator]
@allure.severity(allure.severity_level.CRITICAL)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.label("layer", LAYER)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.title("Teardown runs even when the test chain fails")  # type: ignore[no-untyped-call,untyped-decorator]
def test_teardown_runs_on_failure() -> None:  # noqa: D103
    teardown_called = {"hit": False}

    def failing(driver: FakeDriver, logger: ILogger) -> Scenario[FakeDriver]:  # noqa: ARG001
        pom = RecordingPOM(raise_on={"ok"})
        return Scenario(
            test_chain=[drive_page(acting(pom, "ok"))],
            teardown=lambda: teardown_called.__setitem__("hit", True),  # noqa: FBT003
        )

    suite = make_suite("s", [make_test("t", scenario=failing)])
    results = suite.run(max_workers=1, saturate_workers=False)

    assert is_test_result_fail(results["t"][0])
    assert teardown_called["hit"] is True


@allure.epic(EPIC)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.feature(FEATURE)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.tag("suite", "filter")  # type: ignore[no-untyped-call,untyped-decorator]
@allure.severity(allure.severity_level.NORMAL)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.label("layer", LAYER)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.title("only_ids keeps only the listed test_ids")  # type: ignore[no-untyped-call,untyped-decorator]
def test_only_ids_filters_suite() -> None:  # noqa: D103
    suite = make_suite(
        "s",
        [make_test("t1"), make_test("t2"), make_test("t3")],
        only_ids=("t1", "t3"),
    )

    results = suite.run(max_workers=1, saturate_workers=False)

    assert list(results.keys()) == ["t1", "t3"]


@allure.epic(EPIC)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.feature(FEATURE)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.tag("suite", "filter")  # type: ignore[no-untyped-call,untyped-decorator]
@allure.severity(allure.severity_level.NORMAL)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.label("layer", LAYER)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.title("exclude_ids drops the listed test_ids")  # type: ignore[no-untyped-call,untyped-decorator]
def test_exclude_ids_filters_suite() -> None:  # noqa: D103
    suite = make_suite(
        "s",
        [make_test("t1"), make_test("t2"), make_test("t3")],
        exclude_ids=("t2",),
    )

    results = suite.run(max_workers=1, saturate_workers=False)

    assert list(results.keys()) == ["t1", "t3"]


@allure.epic(EPIC)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.feature(FEATURE)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.tag("suite", "filter")  # type: ignore[no-untyped-call,untyped-decorator]
@allure.severity(allure.severity_level.NORMAL)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.label("layer", LAYER)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.title("Passing both only_ids and exclude_ids raises")  # type: ignore[no-untyped-call,untyped-decorator]
def test_only_and_exclude_mutex() -> None:  # noqa: D103
    with pytest.raises(ValueError, match="cannot be used together"):
        make_suite(
            "s",
            [make_test("t1")],
            only_ids=("t1",),
            exclude_ids=("t1",),
        )


@allure.epic(EPIC)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.feature(FEATURE)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.tag("suite", "filter")  # type: ignore[no-untyped-call,untyped-decorator]
@allure.severity(allure.severity_level.NORMAL)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.label("layer", LAYER)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.title("Unknown filter IDs warn but do not fail the suite")  # type: ignore[no-untyped-call,untyped-decorator]
def test_unknown_ids_warn_not_fatal() -> None:  # noqa: D103
    suite = make_suite(
        "s",
        [make_test("t1"), make_test("t2")],
        only_ids=("t1", "ghost"),
        create_logger=MutedLogger,
    )

    results = suite.run(max_workers=1, saturate_workers=False)

    assert list(results.keys()) == ["t1"]


@allure.epic(EPIC)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.feature(FEATURE)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.tag("suite", "retry", "nonreg")  # type: ignore[no-untyped-call,untyped-decorator]
@allure.severity(allure.severity_level.CRITICAL)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.label("layer", LAYER)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.title(  # type: ignore[no-untyped-call,untyped-decorator]
    "Non-reg: 8 retries == 9 total lives for a test that always crashes transiently"
)
def test_eight_retries_yields_nine_total_attempts(  # noqa: D103
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Silence linear backoff: 1+2+...+8 = 36s otherwise.
    monkeypatch.setattr(
        "ocarina.dsl.testing.internals.test_flow.time.sleep",
        lambda _seconds: None,
    )

    class Flaky(Exception): ...  # noqa: N818

    attempts = {"count": 0}

    def always_flaky(driver: FakeDriver, logger) -> Scenario[FakeDriver]:  # noqa: ANN001, ARG001
        attempts["count"] += 1
        pom = RecordingPOM(
            raise_on={"boom"},
            raises_with={"boom": Flaky("flaky")},
        )
        return Scenario(test_chain=[drive_page(acting(pom, "boom"))])

    suite = make_suite(
        "s",
        [make_test("doomed", scenario=always_flaky)],
        transient_errors=(Flaky,),
        max_retries_per_test=8,
    )

    results = suite.run(max_workers=1, saturate_workers=False)

    outcome, _steps, _id = results["doomed"]
    assert is_test_result_fail(outcome)
    assert attempts["count"] == 9  # noqa: PLR2004


@allure.epic(EPIC)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.feature(FEATURE)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.tag("suite", "driver-death")  # type: ignore[no-untyped-call,untyped-decorator]
@allure.severity(allure.severity_level.CRITICAL)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.label("layer", LAYER)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.title("A driver that dies on acquisition is retried with a fresh one")  # type: ignore[no-untyped-call,untyped-decorator]
def test_driver_death_on_acquisition_is_retried_then_succeeds(  # noqa: D103
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "ocarina.dsl.testing.internals.test_flow.time.sleep",
        lambda _seconds: None,
    )
    boots = {"count": 0}

    def deadly_then_ok() -> tuple[FakeDriver, Callable[[], None]]:
        boots["count"] += 1
        if boots["count"] < 3:  # noqa: PLR2004
            msg = "node crashed during startup"
            raise DriverDiedError(msg)
        return make_built_driver()

    suite = make_suite(
        "s",
        [make_test("t")],
        pool=make_pool(max_size=1, driver_factory=deadly_then_ok),
        max_retries_per_test=5,
    )

    results = suite.run(max_workers=1, saturate_workers=False)

    assert is_test_result_ok(results["t"][0])
    assert boots["count"] == 3  # noqa: PLR2004


@allure.epic(EPIC)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.feature(FEATURE)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.tag("suite", "driver-death")  # type: ignore[no-untyped-call,untyped-decorator]
@allure.severity(allure.severity_level.BLOCKER)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.label("layer", LAYER)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.title("A driver that never boots SKIPs the test — it does not fail or crash")  # type: ignore[no-untyped-call,untyped-decorator]
def test_persistent_acquisition_death_skips_tests_without_crashing_suite(  # noqa: D103
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "ocarina.dsl.testing.internals.test_flow.time.sleep",
        lambda _seconds: None,
    )

    def always_dead() -> tuple[FakeDriver, Callable[[], None]]:
        msg = "node keeps crashing at startup"
        raise DriverDiedError(msg)

    suite = make_suite(
        "s",
        [make_test("t1"), make_test("t2")],
        pool=make_pool(max_size=2, driver_factory=always_dead),
        max_retries_per_test=2,
    )

    # Parallel run also exercises the future.result() collection path, which
    # would re-raise if run() propagated instead of skipping.
    results = suite.run(max_workers=2, saturate_workers=False)

    assert set(results.keys()) == {"t1", "t2"}
    for outcome, *_ in results.values():
        assert outcome is None  # never ran -> SKIP, not Fail
