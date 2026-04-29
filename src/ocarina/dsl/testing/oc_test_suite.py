"""Test suite orchestration with parallel execution.

Supports single/multi-threaded execution, worker saturation, per-test logging,
screenshot capture on failure, and automatic retry on transient errors.

Execution and retry logic are delegated to TestExecutor and TestFlow.
TestSuite is responsible only for validation, worker saturation, and
dispatching tests across threads.
"""

import copy
import logging
import random
import time
from concurrent.futures import FIRST_COMPLETED, ThreadPoolExecutor, wait
from typing import TYPE_CHECKING

from ocarina.custom_invariants.testing.oc_test_runners_ids import (
    validate_test_runners_ids,
)
from ocarina.custom_invariants.testing.oc_test_runners_names import (
    validate_test_runners_names,
)
from ocarina.custom_invariants.testing.workers import validate_workers_amount
from ocarina.dsl.testing.filter_tests_by_ids import filter_tests_by_ids
from ocarina.dsl.testing.internals.test_executor import TestExecutor
from ocarina.dsl.testing.internals.test_flow import TestFlow
from ocarina.infra.drivers_pool import WarmupTimeoutError
from ocarina.opinionated.infra.act_counter import ActCounter as ThreadsBasedActCounter

if TYPE_CHECKING:
    from collections.abc import Iterable, Sequence

    from ocarina.custom_types.oc_test_layers import (
        TestId,
        TestSuiteResults,
    )
    from ocarina.custom_types.thunk import Thunk
    from ocarina.dsl.testing.oc_test import Test
    from ocarina.infra.act_counter import ActCounter
    from ocarina.infra.drivers_pool import WebDriversPool
    from ocarina.ports.ilogger import ILogger
    from ocarina.ports.itake_screenshot import ITakeScreenshot

_DEFAULT_MAX_RETRIES_PER_TEST = 8


class TestSuite[Driver]:
    """Orchestrator for a sequence of related tests.

    Handles parallel execution, worker saturation, and result aggregation.
    Per-test retry logic is owned by TestFlow.
    Per-attempt execution is owned by TestExecutor.

    Transient errors trigger automatic retry with linear backoff (see TestFlow).
    Assertion/business failures fail immediately without retry.
    """

    def _guards_with_mounted_tests(self, tests: Sequence[Test[Driver]]) -> None:
        """Validate test names are unique (including [COPY N] duplicates)."""
        validate_test_runners_names(
            tests=tests, name="tests"
        ).execute().raise_if_invalid()

    def _guards_on_invoke(self, tests: Sequence[Test[Driver]]) -> None:
        """Validate original test IDs are unique."""
        validate_test_runners_ids(
            tests=tests, name="tests"
        ).execute().raise_if_invalid()

    def __init__(  # noqa: PLR0913
        self,
        *,
        name: str,
        tests: Sequence[Test[Driver]],
        create_logger: Thunk[ILogger],
        drivers_pool: WebDriversPool[Driver],
        take_screenshot: ITakeScreenshot[Driver],
        act_counter: ActCounter | None = None,
        transient_errors: tuple[type[Exception], ...] = (),
        copy_indicator: str = "COPY",
        put_space_after_copy_indicator: bool = True,
        max_retries_per_test: int | None = None,
        autoscreen_on_fail: bool = False,
        saturate_workers: bool | None = None,
        only_ids: Iterable[str] = (),
        exclude_ids: Iterable[str] = (),
    ) -> None:
        """Initialize test suite.

        Args:
            name: Suite name used in logs and reports.
            tests: Tests to execute. Must have unique test_id values.
            create_logger: Factory called per test to create an isolated logger.
            drivers_pool: Thread-safe pool of driver instances.
            take_screenshot: Callable (driver, logger, category) -> None.
            act_counter: Tracks act() call count per test execution.
            transient_errors: Exception types that trigger retry. Default: ().
            copy_indicator: Prefix for duplicated tests. Default: "COPY" -> "[COPY 1]".
            put_space_after_copy_indicator: "[COPY 1]" vs "[COPY1]". Default: True.
            max_retries_per_test: Max retry attempts on transient failures. Default: 8.
            autoscreen_on_fail: Capture screenshot automatically on test failure.
            saturate_workers: Duplicate tests to reach max_workers. Default: None.
            only_ids: If non-empty, keep only tests whose test_id is in this set.
                     Mutually exclusive with exclude_ids.
            exclude_ids: If non-empty, drop tests whose test_id is in this set.
                        Mutually exclusive with only_ids.

        Raises:
            ValueError: If both only_ids and exclude_ids are non-empty.

        """
        self._guards_on_invoke(tests)

        self.name = name
        self._create_logger = create_logger
        self._drivers_pool = drivers_pool
        self._take_screenshot = take_screenshot
        self._act_counter = act_counter or ThreadsBasedActCounter()
        self._transient_errors = transient_errors
        self._results: TestSuiteResults = {}
        self._copy_indicator = copy_indicator
        self._put_space_after_copy_indicator = put_space_after_copy_indicator
        self._max_retries_per_test = (
            _DEFAULT_MAX_RETRIES_PER_TEST
            if max_retries_per_test is None
            else max_retries_per_test
        )
        self._autoscreen_on_fail = autoscreen_on_fail
        self._saturate_workers = saturate_workers

        self._campaign_name: str = ""
        self._cycle_name: str = ""

        self._tests = filter_tests_by_ids(
            tests,
            only=only_ids,
            exclude=exclude_ids,
            logger=create_logger().set_prefix(
                lambda: f"{self.name}: filtering tests..."
            ),
        )

    def _build_flow(self) -> TestFlow[Driver]:
        """Construct a TestFlow wired to this suite's dependencies."""
        return TestFlow(
            executor=TestExecutor(
                create_logger=self._create_logger,
                take_screenshot=self._take_screenshot,
                act_counter=self._act_counter,
                transient_errors=self._transient_errors,
                autoscreen_on_fail=self._autoscreen_on_fail,
            ),
            drivers_pool=self._drivers_pool,
            create_logger=self._create_logger,
            act_counter=self._act_counter,
            cycle_name=self._cycle_name,
            campaign_name=self._campaign_name,
            suite_name=self.name,
            max_retries=self._max_retries_per_test,
        )

    def _prepare_tests_for_saturated_threading(
        self, max_workers: int
    ) -> Sequence[Test[Driver]]:
        """Duplicate tests randomly until count reaches max_workers.

        Copies are named "[COPY N] original_name".
        """
        base_tests = list(self._tests)

        if len(base_tests) == 0:
            return base_tests

        extra_tests: list[Test[Driver]] = []
        copy_counters: dict[str, int] = {}

        for _ in range(max_workers - len(base_tests)):
            original = random.choice(base_tests)  # noqa: S311
            copy_counters.setdefault(original.name, 0)
            copy_counters[original.name] += 1

            cloned = copy.copy(original)
            space = " " if self._put_space_after_copy_indicator else ""
            cloned.name = (
                f"[{self._copy_indicator}{space}{copy_counters[original.name]}]"
                f" {original.name}"
            )
            extra_tests.append(cloned)

        return base_tests + extra_tests

    @property
    def test_names_and_ids(self) -> Sequence[tuple[str, TestId]]:
        """Return (name, test_id) pairs for all tests in the suite."""
        return [(test.name, test.test_id) for test in self._tests]

    def run(
        self,
        *,
        max_workers: int,
        saturate_workers: bool = True,
    ) -> TestSuiteResults:
        """Execute all tests. Returns dict mapping test name -> TestSuiteResult.

        Args:
            max_workers: Concurrent workers. 1 = sequential execution.
            saturate_workers: Duplicate tests to reach max_workers. Default: True.

        Raises:
            AggregateInvariantViolationError: If max_workers < 1 or duplicate names.

        """
        self._results.clear()

        validate_workers_amount(
            workers_amount=max_workers, name="max_workers"
        ).execute().raise_if_invalid()

        resolved_saturate_workers = (
            self._saturate_workers
            if self._saturate_workers is not None
            else saturate_workers
        )

        flow = self._build_flow()

        if max_workers == 1:
            for test in self._tests:
                self._results[test.name] = flow.run(test)
        else:
            if resolved_saturate_workers and len(self._tests) > 0:
                try:
                    self._drivers_pool.warmup()
                except WarmupTimeoutError:
                    logging.basicConfig(level=logging.INFO)
                    logger = logging.getLogger(__name__)
                    logger.info(
                        "Warmup stalled: killing the program. Expect it to raise soon."
                        " "
                        "Cleanup will be attempted"
                        " "
                        "but some browser processes may survive."
                        " "
                        "Check Activity Monitor / Dock for remaining instances."
                    )
                    time.sleep(30)
                    self._drivers_pool.shutdown()
                    time.sleep(5)
                    raise
                tests = self._prepare_tests_for_saturated_threading(
                    max_workers=max_workers
                )
            else:
                tests = self._tests

            self._guards_with_mounted_tests(tests)

            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                futures = {
                    executor.submit(flow.run, test): (test.name, test.test_id)
                    for test in tests
                }

                while futures:
                    done, _ = wait(futures, return_when=FIRST_COMPLETED)
                    for future in done:
                        name, _ = futures.pop(future)
                        self._results[name] = future.result()

        return self._results
