"""Validation of campaigns names: unique and valid cross-platform filenames."""

import unicodedata
from typing import TYPE_CHECKING

from ocarina.dsl.invariants.assertions import (
    each,
    has_unique_elements,
    is_valid_filename,
)
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
    return chain.assert_that(
        has_unique_elements(
            key=lambda c: unicodedata.normalize("NFC", c.name).casefold()
        ),
        msg="Campaigns names must be unique (case-insensitive).",
    ).assert_that(
        each(lambda c: is_valid_filename(c.name)),
        msg="Test campaigns names must be valid cross-platform filenames.",
    )


def validate_campaigns_names[Driver](
    *, campaigns: Sequence[TestCampaign[Driver]], name: str
) -> ValidationAssertBlock[Sequence[TestCampaign[Driver]]]:
    """Validate that campaigns names are unique and valid cross-platform filenames."""
    return FrameworkInvariantValidator.create(campaigns, name, _campaigns_names)
