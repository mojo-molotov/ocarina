"""Single-attempt test execution.

TestExecutor knows nothing about retries, pools, or concurrency.
It executes exactly one attempt of a test and returns a structured outcome.
"""

from contextlib import suppress
from dataclasses import dataclass
from typing import TYPE_CHECKING, final

from ocarina.aggregates.tests_layers import is_test_result_fail
from ocarina.dsl.testing_with_railway.internals.action_chain import ActionChain
from ocarina.railway.result import Fail

if TYPE_CHECKING:
    from collections.abc import Sequence

    from ocarina.custom_types.effect import Effect
    from ocarina.custom_types.oc_test_layers import TestResult
    from ocarina.custom_types.test_components import TestChain
    from ocarina.custom_types.thunk import Thunk
    from ocarina.dsl.testing.oc_test import Test
    from ocarina.dsl.testing.watcher import Watcher
    from ocarina.infra.act_counter import ActCounter
    from ocarina.ports.ilogger import ILogger
    from ocarina.ports.itake_screenshot import ITakeScreenshot


@final
@dataclass(frozen=True, slots=True)
class ExecutionOutcome:
    """Result of a single test attempt.

    Attributes:
        result:         The TestResult produced by the chain. None if setup failed
                        or test was skipped.
        skipped:        True when the test declared itself skipped via spawn().
        setup_failed:   True when setup() raised before the chain could run.
        should_retry:   True when the failure is transient and a retry is warranted.
        steps_count:    Number of act() calls recorded during this attempt.
                        -1 when the test was skipped or setup failed.

    """

    result: TestResult
    skipped: bool
    setup_failed: bool
    should_retry: bool
    steps_count: int


@final
class TestExecutor[Driver]:
    """Executes one attempt of a test.

    Execution order:
        1. setup()           -- optional; skips chain on failure
        2. watchers.start()  -- started just before test_chain
        3. test_chain        -- the actual test steps
        4. watchers.stop()   -- stopped immediately after test_chain
        5. teardown()        -- always runs, even on failure

    Watchers are strictly scoped to test_chain. They do not observe
    setup or teardown -- those are infrastructure concerns.
    """

    def __init__(
        self,
        *,
        create_logger: Thunk[ILogger],
        take_screenshot: ITakeScreenshot[Driver],
        act_counter: ActCounter,
        transient_errors: tuple[type[Exception], ...] = (),
        autoscreen_on_fail: bool = False,
    ) -> None:
        """Initialise the executor.

        Args:
            create_logger:      Factory called to produce a fresh logger.
                                Used to build per-watcher scoped loggers.
            take_screenshot:    Callable (driver, logger, category) -> None.
            act_counter:        Tracks act() calls. The caller (TestFlow) is
                                responsible for resetting it before each attempt.
            transient_errors:   Exception types that hint the caller to retry.
            autoscreen_on_fail: Capture screenshot automatically on chain failure.

        """
        self._create_logger = create_logger
        self._take_screenshot = take_screenshot
        self._act_counter = act_counter
        self._transient_errors = transient_errors
        self._autoscreen_on_fail = autoscreen_on_fail

    def execute(  # noqa: PLR0913
        self,
        test: Test[Driver],
        *,
        driver: Driver,
        taxonomy: tuple[str, ...],
        logger_with_taxonomy: ILogger,
        logger_without_taxonomy: ILogger,
        attempt: int,
        max_attempts: int,
    ) -> ExecutionOutcome:
        """Run one attempt of *test* against *driver*.

        Args:
            test:                    The test to execute.
            driver:                  Live driver for this attempt.
            taxonomy:                Domain taxonomy tuple passed explicitly by the
                                     caller (e.g. (campaign, suite, test_name)).
                                     Used to scope per-watcher loggers without
                                     introspecting logger internals.
            logger_with_taxonomy:    Logger already scoped to *taxonomy*.
                                     Used for structured reporting.
            logger_without_taxonomy: Flat logger used for test_name() bookkeeping.
            attempt:                 Current attempt number (1-based).
            max_attempts:            Total allowed attempts (used for retry hint).

        Returns:
            ExecutionOutcome describing what happened.

        """
        test_runner = test.spawn(driver, logger_with_taxonomy)

        if test_runner.skipped:
            return ExecutionOutcome(
                result=None,
                skipped=True,
                setup_failed=False,
                should_retry=False,
                steps_count=-1,
            )

        logger_without_taxonomy.test_name(test.name)

        if test_runner.setup is not None:
            try:
                test_runner.setup()
            except Exception as exc:  # noqa: BLE001
                msg = (
                    f"{test.name} -- Setup failed"
                    f" (attempt {attempt}/{max_attempts}): {exc}"
                )
                logger_with_taxonomy.warning(msg)
                if test_runner.teardown is not None:
                    self._run_teardown(
                        test_runner.teardown,
                        test_name=test.name,
                        logger=logger_with_taxonomy,
                    )
                return ExecutionOutcome(
                    result=None,
                    skipped=False,
                    setup_failed=True,
                    should_retry=True,
                    steps_count=-1,
                )

        watchers: Sequence[Watcher[Driver]] = test_runner.watchers or []
        self._start_watchers(
            watchers,
            driver=driver,
            test_name=test.name,
            taxonomy=taxonomy,
        )

        result, should_retry = self._run_chain(
            test_runner.chain_runners,
            test_name=test.name,
            attempt=attempt,
            driver=driver,
            logger=logger_without_taxonomy,
            logger_with_taxonomy=logger_with_taxonomy,
            max_attempts=max_attempts,
        )

        self._stop_watchers(watchers)

        if test_runner.teardown is not None:
            self._run_teardown(
                test_runner.teardown,
                test_name=test.name,
                logger=logger_with_taxonomy,
            )

        steps_count = self._act_counter.get()

        return ExecutionOutcome(
            result=result,
            skipped=False,
            setup_failed=False,
            should_retry=should_retry,
            steps_count=steps_count,
        )

    def _run_chain(  # noqa: PLR0913
        self,
        chain_runners: TestChain,
        *,
        test_name: str,
        attempt: int,
        driver: Driver,
        logger: ILogger,
        logger_with_taxonomy: ILogger,
        max_attempts: int,
    ) -> tuple[TestResult, bool]:
        """Run the chain runners in order. Returns (result, should_retry)."""
        result: TestResult = None

        for chain_runner in chain_runners:
            try:
                chain = chain_runner.run()
            except Exception as exc:  # noqa: BLE001
                chain = ActionChain(has_failed=True, result=Fail(error=exc))
            result = chain.result()

            if chain.has_failed():
                if (
                    attempt < max_attempts
                    and self._transient_errors
                    and is_test_result_fail(result)
                    and isinstance(result.error, self._transient_errors)
                ):
                    msg = f"{test_name} -- Test died! Life: {attempt}/{max_attempts}"
                    logger.warning(msg)
                    return result, True

                if self._autoscreen_on_fail and is_test_result_fail(result):
                    with suppress(Exception):
                        self._take_screenshot(driver, logger_with_taxonomy, "FAIL")

                return result, False

        return result, False

    def _run_teardown(
        self,
        teardown: Effect,
        *,
        test_name: str,
        logger: ILogger,
    ) -> None:
        """Run teardown. Always executes. Failures are logged and ignored."""
        try:
            teardown()
        except Exception as exc:  # noqa: BLE001
            msg = f"{test_name} -- Teardown failed (ignored): {exc}"
            logger.warning(msg)

    def _start_watchers(
        self,
        watchers: Sequence[Watcher[Driver]],
        *,
        driver: Driver,
        test_name: str,
        taxonomy: tuple[str, ...],
    ) -> None:
        """Start all watchers. Failures are suppressed.

        Each watcher gets a fresh logger scoped to (*taxonomy, suffix) where
        suffix is "test_name - watcher_name", prefixed with the watcher index
        when multiple watchers are present: "[1] test_name - watcher_name".
        """
        for index, watcher in enumerate(watchers):
            with suppress(Exception):
                watcher_name = (
                    f"[{index + 1}] {test_name} - {watcher.name}"
                    if len(watchers) > 1
                    else f"{test_name} - {watcher.name}"
                )
                watcher_taxonomy = (*taxonomy[:-1], watcher_name)
                scoped_logger = self._create_logger().set_domain_taxonomy(
                    watcher_taxonomy
                )
                watcher.start(driver, scoped_logger, self._take_screenshot)

    def _stop_watchers(self, watchers: Sequence[Watcher[Driver]]) -> None:
        """Stop all watchers. Failures are suppressed."""
        for watcher in watchers:
            with suppress(Exception):
                watcher.stop()
