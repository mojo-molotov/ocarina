"""Test encapsulation.

Lifecycle: Definition → Registration → Spawn
Driver is inferred.
"""

from typing import TYPE_CHECKING, Any, final

from ocarina.custom_types.test_runner import TestRunner

if TYPE_CHECKING:
    from collections.abc import Sequence

    from ocarina.custom_types.oc_test import (
        TestName,
        TestScenario,
        TestScenarioFragment,
    )
    from ocarina.dsl.testing_with_railway.chain_actions import ChainRunner
    from ocarina.ports.ilogger import ILogger


@final
class Test[Driver]:
    """Single test case: metadata + scenario factory.

    spawn() injects runtime dependencies (driver, logger) into the scenario.
    """

    def __init__(  # noqa: PLR0913
        self,
        *,
        name: TestName,
        test_id: str | None = None,
        test_scenario: TestScenario[Driver],
        pre_test_scenarios_fragments: Sequence[TestScenarioFragment[Driver]]
        | None = None,
        post_test_scenarios_fragments: Sequence[TestScenarioFragment[Driver]]
        | None = None,
        skipped: bool = False,
    ) -> None:
        """Test builder.

        Args:
            name: Human-readable label used in logs and reports.
            test_id: Stable unique identifier. Defaults to name.
            test_scenario: Scenario factory (Driver, ILogger) → chains.
            pre_test_scenarios_fragments: Setup scenarios fragments run before scenario.
            post_test_scenarios_fragments: Setup scenarios fragments run after scenario.
            skipped: If True, test is registered but not executed.

        """
        if test_id is None:
            test_id = name

        self.name = name
        self.test_id = test_id
        self._test_scenario = test_scenario
        self._pre_test_scenarios_fragments = pre_test_scenarios_fragments or []
        self._post_test_scenarios_fragments = post_test_scenarios_fragments or []
        self._skipped = skipped

    def spawn(self, driver: Driver, logger: ILogger) -> TestRunner[Driver]:
        """Instantiate chains with (driver, logger). Returns TestRunner."""
        chain_runners: list[ChainRunner[Any]] = []

        for pre_chain in self._pre_test_scenarios_fragments:
            chain_runners.extend(pre_chain(driver, logger))

        scenario = self._test_scenario(driver, logger)
        chain_runners.extend(scenario.test_chain)

        for post_chain in self._post_test_scenarios_fragments:
            chain_runners.extend(post_chain(driver, logger))

        return TestRunner(
            chain_runners=chain_runners,
            skipped=self._skipped,
            setup=scenario.setup,
            teardown=scenario.teardown,
            watchers=scenario.watchers,
        )
