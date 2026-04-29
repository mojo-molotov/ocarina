"""Retry-loop orchestration for a single test.

TestFlow owns the retry/backoff policy and driver acquisition.
It delegates the actual execution of each attempt to TestExecutor.
"""

import time
from typing import TYPE_CHECKING, final

if TYPE_CHECKING:
    from ocarina.custom_types.oc_test_layers import TestSuiteResult
    from ocarina.custom_types.thunk import Thunk
    from ocarina.dsl.testing.internals.test_executor import TestExecutor
    from ocarina.dsl.testing.oc_test import Test
    from ocarina.infra.act_counter import ActCounter
    from ocarina.infra.drivers_pool import WebDriversPool
    from ocarina.ports.ilogger import ILogger

_DEFAULT_MAX_RETRIES = 8


@final
class TestFlow[Driver]:
    """Retry loop for a single test.

    Responsibilities:
        - Acquire / release a driver for each attempt via the pool.
        - Build the two loggers (with/without taxonomy) per attempt.
        - Apply the retry policy: backoff, max attempts, setup-failure tracking.
        - Delegate actual execution to TestExecutor.

    It knows nothing about concurrency or test-suite aggregation — that belongs
    to TestSuite.

    Retry policy:
        total_attempts = 1 + max_retries
        After a transient failure the flow sleeps `attempt` seconds (linear
        backoff) then retries.  If setup fails on every attempt the test is
        treated as skipped.
    """

    def __init__(  # noqa: PLR0913
        self,
        *,
        executor: TestExecutor[Driver],
        drivers_pool: WebDriversPool[Driver],
        create_logger: Thunk[ILogger],
        act_counter: ActCounter,
        cycle_name: str,
        campaign_name: str,
        suite_name: str,
        max_retries: int = _DEFAULT_MAX_RETRIES,
    ) -> None:
        """Initialize the flow.

        Args:
            executor:       TestExecutor that handles one attempt.
            drivers_pool:   Thread-safe pool; one driver is acquired per attempt.
            create_logger:  Factory called to produce a fresh logger per attempt.
            act_counter:    Shared counter reset before each attempt.
            cycle_name:     Taxonomy level injected into the scoped logger.
            campaign_name:  Taxonomy level injected into the scoped logger.
            suite_name:     Taxonomy level injected into the scoped logger.
            max_retries:    Number of *additional* attempts after the first one.
                            Total attempts = 1 + max_retries. Default: 8.

        """
        self._executor = executor
        self._drivers_pool = drivers_pool
        self._create_logger = create_logger
        self._act_counter = act_counter
        self._cycle_name = cycle_name
        self._campaign_name = campaign_name
        self._suite_name = suite_name
        self._max_retries = max_retries

    def run(self, test: Test[Driver]) -> TestSuiteResult:
        """Execute *test* with retry. Returns (TestResult, steps_count, test_id).

        Skipped tests and all-setup-failure tests return (None, -1, test_id).
        """
        max_attempts = 1 + self._max_retries
        setup_failures = 0
        last_steps_count = -1
        last_result = None

        taxonomy = (self._cycle_name, self._campaign_name, self._suite_name, test.name)
        logger_with_taxonomy = self._create_logger().set_domain_taxonomy(taxonomy)
        logger_without_taxonomy = self._create_logger()

        for attempt in range(1, max_attempts + 1):
            self._act_counter.reset()

            with self._drivers_pool.acquire() as driver:
                outcome = self._executor.execute(
                    test,
                    driver=driver,
                    taxonomy=taxonomy,
                    logger_with_taxonomy=logger_with_taxonomy,
                    logger_without_taxonomy=logger_without_taxonomy,
                    attempt=attempt,
                    max_attempts=max_attempts,
                )

            if outcome.skipped:
                return None, -1, test.test_id

            if outcome.setup_failed:
                setup_failures += 1

            last_result = outcome.result
            last_steps_count = outcome.steps_count

            if outcome.should_retry and attempt < max_attempts:
                logger_with_taxonomy.cleanup()
                time.sleep(attempt)
                continue

            break

        if setup_failures >= max_attempts:
            msg = (
                f"{test.name} — Skipped: setup failed on all"
                f" {max_attempts} attempts. Fix the setup before retrying."
            )
            logger_with_taxonomy.warning(msg)
            return None, -1, test.test_id

        self._act_counter.reset()
        return last_result, last_steps_count, test.test_id
