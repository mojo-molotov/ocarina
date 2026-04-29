"""Create a Test bound to Selenium WebDriver."""

from typing import TYPE_CHECKING

from ocarina.dsl.testing.oc_test import Test

if TYPE_CHECKING:
    from collections.abc import Sequence

    from selenium.webdriver.remote.webdriver import WebDriver

    from ocarina.custom_types.oc_test import (
        TestName,
        TestScenario,
        TestScenarioFragment,
    )


def create_selenium_test(  # noqa: PLR0913
    *,
    name: TestName,
    test_id: str | None = None,
    test_scenario: TestScenario[WebDriver],
    pre_test_scenarios_fragments: Sequence[TestScenarioFragment[WebDriver]]
    | None = None,
    post_test_scenarios_fragments: Sequence[TestScenarioFragment[WebDriver]]
    | None = None,
    skipped: bool = False,
):
    """Create a Test bound to Selenium WebDriver."""
    return Test(
        name=name,
        test_id=test_id,
        test_scenario=test_scenario,
        pre_test_scenarios_fragments=pre_test_scenarios_fragments,
        post_test_scenarios_fragments=post_test_scenarios_fragments,
        skipped=skipped,
    )
