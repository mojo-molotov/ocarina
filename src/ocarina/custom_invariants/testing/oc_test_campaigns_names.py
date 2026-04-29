"""Validation of campaigns names: must be unique."""

from typing import TYPE_CHECKING

from ocarina.dsl.invariants.assertions import has_unique_elements
from ocarina.dsl.invariants.validate import FrameworkInvariantValidator

if TYPE_CHECKING:
    from collections.abc import Sequence

    from ocarina.dsl.invariants.internals.validation_chain import (
        ValidationAssertBlock,
        ValidationStartBlock,
    )
    from ocarina.dsl.testing.oc_test_campaign import TestCampaign


def _campaigns_names[Driver](
    chain: ValidationStartBlock[Sequence[TestCampaign[Driver]]],
    _: Sequence[TestCampaign[Driver]],
) -> ValidationAssertBlock[Sequence[TestCampaign[Driver]]]:
    def get_campaign_name(c: TestCampaign[Driver]) -> str:
        return c.name

    return chain.assert_that(
        has_unique_elements(key=get_campaign_name),
        msg="Campaigns names must be unique.",
    )


def validate_campaigns_names[Driver](
    *, campaigns: Sequence[TestCampaign[Driver]], name: str
) -> ValidationAssertBlock[Sequence[TestCampaign[Driver]]]:
    """Validate that all campaigns names are unique."""
    return FrameworkInvariantValidator.create(campaigns, name, _campaigns_names)
