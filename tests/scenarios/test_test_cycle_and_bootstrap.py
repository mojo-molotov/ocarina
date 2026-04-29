"""TestCycle + bootstrap: smoke→main ordering, cycle-level failure, plugin isolation."""

# ruff: noqa: S101

from typing import Never

import allure

from ocarina.dsl.testing.oc_test_cycle import has_test_cycle_failed
from ocarina.opinionated.launcher.bootstrap import bootstrap, run_plugins
from ocarina.opinionated.loggers.muted_logger import MutedLogger

from .conftest import (
    failing_scenario,
    make_campaign,
    make_cycle,
    make_suite,
    make_test,
)

EPIC = "TestCycle & bootstrap"
FEATURE = "Cycle & bootstrap"
LAYER = "integration"


@allure.epic(EPIC)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.feature(FEATURE)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.tag("cycle", "happy-path")  # type: ignore[no-untyped-call,untyped-decorator]
@allure.severity(allure.severity_level.CRITICAL)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.label("layer", LAYER)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.title("All-green cycle: every test is Ok and has_test_cycle_failed is False")  # type: ignore[no-untyped-call,untyped-decorator]
def test_all_green_cycle() -> None:  # noqa: D103
    cycle = make_cycle(
        campaigns=[
            make_campaign(
                "main",
                [make_suite("s", [make_test("t1"), make_test("t2")])],
            ),
        ],
    )

    results = cycle.run_all(saturate_workers=False)

    assert has_test_cycle_failed(results) is False


@allure.epic(EPIC)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.feature(FEATURE)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.tag("cycle", "smoke")  # type: ignore[no-untyped-call,untyped-decorator]
@allure.severity(allure.severity_level.BLOCKER)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.label("layer", LAYER)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.title("A failing smoke causes the main campaigns to be skipped (fail-fast)")  # type: ignore[no-untyped-call,untyped-decorator]
def test_failing_smoke_skips_main() -> None:  # noqa: D103
    main_executed = {"count": 0}

    def tracking_scenario(driver, logger):  # noqa: ANN001, ANN202, ARG001
        main_executed["count"] += 1
        from ocarina.custom_types.scenario import Scenario  # noqa: PLC0415

        return Scenario(test_chain=[])

    cycle = make_cycle(
        smoke=[
            make_campaign(
                "smoke",
                [
                    make_suite(
                        "s",
                        [make_test("smk", scenario=failing_scenario())],
                    )
                ],
            ),
        ],
        campaigns=[
            make_campaign(
                "main",
                [
                    make_suite(
                        "s2",
                        [make_test("m1", scenario=tracking_scenario)],
                    )
                ],
            ),
        ],
    )

    results = cycle.run_all(saturate_workers=False)

    # Main test was never actually run
    assert main_executed["count"] == 0
    # Main test outcome is None (skipped)
    main_outcome, _steps, _id = results["main"]["s2"]["m1"]
    assert main_outcome is None
    # Overall cycle still registers as failed due to the smoke failure
    assert has_test_cycle_failed(results) is True


@allure.epic(EPIC)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.feature(FEATURE)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.tag("cycle", "smoke-mode")  # type: ignore[no-untyped-call,untyped-decorator]
@allure.severity(allure.severity_level.NORMAL)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.label("layer", LAYER)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.title(  # type: ignore[no-untyped-call,untyped-decorator]
    "wait-for-all-smoke-tests: every smoke campaign runs even after a failure"
)
def test_wait_for_all_smoke_mode_runs_every_smoke() -> None:  # noqa: D103
    executed: list[str] = []

    def tracker(name: str):  # noqa: ANN202
        def scenario(driver, logger):  # noqa: ANN001, ANN202, ARG001
            executed.append(name)
            from ocarina.custom_types.scenario import Scenario  # noqa: PLC0415

            return Scenario(test_chain=[])

        return scenario

    cycle = make_cycle(
        smoke=[
            make_campaign(
                "smk1",
                [make_suite("s1", [make_test("t1", scenario=failing_scenario())])],
            ),
            make_campaign(
                "smk2",
                [make_suite("s2", [make_test("t2", scenario=tracker("smk2"))])],
            ),
        ],
        campaigns=[
            make_campaign(
                "main",
                [make_suite("s3", [make_test("t3", scenario=tracker("main"))])],
            ),
        ],
        mode="wait-for-all-smoke-tests",
    )

    cycle.run_all(saturate_workers=False)

    # smk2 ran despite smk1 failing; main did not
    assert "smk2" in executed
    assert "main" not in executed


@allure.epic(EPIC)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.feature(FEATURE)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.tag("bootstrap", "ordering")  # type: ignore[no-untyped-call,untyped-decorator]
@allure.severity(allure.severity_level.CRITICAL)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.label("layer", LAYER)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.title("bootstrap runs cycle, then plugins, then post_exec, in order")  # type: ignore[no-untyped-call,untyped-decorator]
def test_bootstrap_calls_plugins_and_post_exec_in_order() -> None:  # noqa: D103
    events: list[str] = []

    cycle = make_cycle(
        campaigns=[
            make_campaign("c", [make_suite("s", [make_test("t")])]),
        ],
    )

    def do_plugins(results) -> None:  # noqa: ANN001, ARG001
        events.append("plugins")

    def post(results) -> None:  # noqa: ANN001, ARG001
        events.append("post")

    bootstrap(
        test_cycle=cycle,
        run_plugins=do_plugins,
        post_exec=post,
        saturate_workers=False,
    )

    assert events == ["plugins", "post"]


@allure.epic(EPIC)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.feature(FEATURE)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.tag("bootstrap", "plugin-isolation")  # type: ignore[no-untyped-call,untyped-decorator]
@allure.severity(allure.severity_level.NORMAL)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.label("layer", LAYER)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.title(  # type: ignore[no-untyped-call,untyped-decorator]
    "run_plugins: one plugin raising does not prevent the others from running"
)
def test_plugin_exception_does_not_block_other_plugins() -> None:  # noqa: D103
    ran: list[str] = []

    def good() -> None:
        ran.append("good")

    def bad() -> Never:
        msg = "plugin boom"
        raise RuntimeError(msg)

    def other() -> None:
        ran.append("other")

    run_plugins(good, bad, other, exceptions_logger=MutedLogger())

    assert set(ran) == {"good", "other"}
