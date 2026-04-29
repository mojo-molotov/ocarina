"""Shared helpers for scenario tests.

Philosophy: exercise the framework from the outside the way a real user does.
No asserts on private attributes, no mocks of framework internals — just a
minimal fake driver + driver pool, and small constructors for Scenario /
Test / TestSuite / TestCampaign / TestCycle.

The fake driver is intentionally tiny: framework core never touches any
Selenium API directly, so a bare object is enough. Page objects get their
own fakes per-test.
"""

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

from ocarina.custom_types.scenario import Scenario
from ocarina.dsl.testing.oc_test import Test
from ocarina.dsl.testing.oc_test_campaign import TestCampaign
from ocarina.dsl.testing.oc_test_cycle import TestCycle
from ocarina.dsl.testing.oc_test_suite import TestSuite
from ocarina.dsl.testing_with_railway.constructors.create_act import create_act
from ocarina.infra.drivers_pool import WebDriversPool
from ocarina.opinionated.dsl.drive_page import drive_page
from ocarina.opinionated.infra.act_counter import ActCounter
from ocarina.opinionated.loggers.muted_logger import MutedLogger
from ocarina.pom.base import POMBase

if TYPE_CHECKING:
    from collections.abc import Callable, Sequence

    from ocarina.custom_types.oc_test import TestScenario
    from ocarina.dsl.testing_with_railway.chain_actions import ChainRunner
    from ocarina.ports.ilogger import ILogger


# --- Fake driver --------------------------------------------------------------


@dataclass
class FakeDriver:
    """Bare driver stand-in. Ocarina's core never touches a driver's API."""

    title: str = "fake"
    disposed: bool = False


def make_built_driver(
    title: str = "fake",
) -> tuple[FakeDriver, Callable[[], None]]:
    """Return (driver, dispose) tuple — Ocarina's BuiltWebDriver shape."""
    driver = FakeDriver(title=title)

    def dispose() -> None:
        driver.disposed = True

    return driver, dispose


def make_pool(
    max_size: int = 2,
    *,
    driver_factory: Callable[[], tuple[FakeDriver, Callable[[], None]]] | None = None,
) -> WebDriversPool[FakeDriver]:
    """Build a pool of FakeDrivers."""
    factory = driver_factory or (make_built_driver)
    return WebDriversPool(create_driver=factory, max_size=max_size)


# --- Tiny POM -----------------------------------------------------------------


@dataclass
class RecordingPOM(POMBase):
    """POM that records every method call and can be configured to raise."""

    calls: list[str] = field(default_factory=list)
    raise_on: set[str] = field(default_factory=set)
    raises_with: dict[str, Exception] = field(default_factory=dict)
    _title: str = "Recording page"

    def verify(self, *, timeout: float | None = None) -> RecordingPOM:  # noqa: ARG002, D102
        return self._do("verify")

    def get_current_title(self) -> str:  # noqa: D102
        return self._title

    def step(self, name: str) -> RecordingPOM:
        """Generic step the scenario can call."""  # noqa: D401
        return self._do(name)

    def _do(self, name: str) -> RecordingPOM:
        self.calls.append(name)
        if name in self.raise_on:
            raise self.raises_with.get(name, RuntimeError(f"{name} failed"))
        return self


# --- Scenario builders --------------------------------------------------------


def acting(pom: RecordingPOM, step: str) -> Any:  # noqa: ANN401
    """Build a fully-configured act (failure + success wired to no-ops)."""
    return (
        create_act(pom, lambda p: p.step(step))
        .failure(lambda exc: None)  # noqa: ARG005
        .success(lambda: None)
    )


def scenario_of(*steps: str) -> TestScenario[FakeDriver]:
    """Build a TestScenario from a list of step names using a fresh RecordingPOM."""

    def factory(driver: FakeDriver, logger: ILogger) -> Scenario[FakeDriver]:  # noqa: ARG001
        pom = RecordingPOM()
        if not steps:
            return Scenario(test_chain=[])
        return Scenario(test_chain=[drive_page(*(acting(pom, s) for s in steps))])

    return factory


def failing_scenario(
    *,
    step: str = "boom",
    exc: Exception | None = None,
) -> TestScenario[FakeDriver]:
    """Scenario whose single step raises."""
    error = exc if exc is not None else RuntimeError("boom")

    def factory(driver: FakeDriver, logger: ILogger) -> Scenario[FakeDriver]:  # noqa: ARG001
        pom = RecordingPOM(raise_on={step}, raises_with={step: error})
        return Scenario(test_chain=[drive_page(acting(pom, step))])

    return factory


# --- Test / Suite / Campaign / Cycle builders ---------------------------------


def make_test(  # noqa: D103
    name: str,
    *,
    scenario: TestScenario[FakeDriver] | None = None,
    test_id: str | None = None,
    skipped: bool = False,
) -> Test[FakeDriver]:
    return Test(
        name=name,
        test_id=test_id,
        test_scenario=scenario or scenario_of("ok"),
        skipped=skipped,
    )


def make_suite(  # noqa: D103, PLR0913
    name: str,
    tests: Sequence[Test[FakeDriver]],
    *,
    pool: WebDriversPool[FakeDriver] | None = None,
    transient_errors: tuple[type[Exception], ...] = (),
    max_retries_per_test: int | None = None,
    only_ids: Sequence[str] = (),
    exclude_ids: Sequence[str] = (),
    create_logger: Callable[[], ILogger] = MutedLogger,
) -> TestSuite[FakeDriver]:
    return TestSuite(
        name=name,
        tests=tests,
        create_logger=create_logger,
        drivers_pool=pool or make_pool(max_size=2),
        take_screenshot=lambda driver, logger, category: None,  # noqa: ARG005
        act_counter=ActCounter(),
        transient_errors=transient_errors,
        max_retries_per_test=max_retries_per_test,
        saturate_workers=False,
        only_ids=only_ids,
        exclude_ids=exclude_ids,
    )


def make_campaign(  # noqa: D103
    name: str,
    suites: Sequence[TestSuite[FakeDriver]],
    *,
    max_workers: int = 1,
) -> TestCampaign[FakeDriver]:
    return TestCampaign(
        name=name,
        suites=suites,
        max_workers=max_workers,
        saturate_workers=False,
    )


def make_cycle(  # noqa: D103
    name: str = "cycle",
    *,
    campaigns: Sequence[TestCampaign[FakeDriver]] = (),
    smoke: Sequence[TestCampaign[FakeDriver]] = (),
    mode: Any = None,  # noqa: ANN401
) -> TestCycle[FakeDriver]:
    return TestCycle(
        name=name,
        campaigns=campaigns,
        smoke_tests_campaigns=smoke,
        mode=mode,
    )


# --- Test runners for small integration checks --------------------------------


def run_chain(runner: ChainRunner[Any]) -> Any:  # noqa: ANN401
    """Execute a ChainRunner and return the resulting ActionChain."""
    return runner.run()
