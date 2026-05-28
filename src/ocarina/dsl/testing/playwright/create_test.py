"""Create a Test bound to Ocarina's PlaywrightDriver."""

from typing import TYPE_CHECKING

from ocarina.dsl.testing.oc_test import Test

if TYPE_CHECKING:
    from collections.abc import Sequence

    from ocarina.custom_types.oc_test import (
        TestName,
        TestScenario,
        TestScenarioFragment,
    )
    from ocarina.infra.playwright.driver import PlaywrightDriver


def create_playwright_test(  # noqa: PLR0913
    *,
    name: TestName,
    test_id: str | None = None,
    test_scenario: TestScenario[PlaywrightDriver],
    pre_test_scenarios_fragments: Sequence[TestScenarioFragment[PlaywrightDriver]]
    | None = None,
    post_test_scenarios_fragments: Sequence[TestScenarioFragment[PlaywrightDriver]]
    | None = None,
    skipped: bool = False,
):
    """Create a Test bound to Ocarina's PlaywrightDriver."""
    return Test(
        name=name,
        test_id=test_id,
        test_scenario=test_scenario,
        pre_test_scenarios_fragments=pre_test_scenarios_fragments,
        post_test_scenarios_fragments=post_test_scenarios_fragments,
        skipped=skipped,
    )
