"""Result of spawning a test."""

from dataclasses import dataclass
from typing import TYPE_CHECKING, final

if TYPE_CHECKING:
    from ocarina.custom_types.test_components import (
        TestChain,
        TestSetup,
        TestTeardown,
        TestWatchers,
    )


@final
@dataclass(frozen=True)
class TestRunner[Driver]:
    """Result of spawning a test — all components needed for execution.

    Attributes:
        chain_runners: Merged sequence of pre, test, and post ChainRunners.
        skipped:       If True, the test is registered but not executed.
        setup:         Optional Effect to run before chain_runners.
        teardown:      Optional Effect to run after chain_runners, always.
        watchers:      Optional concurrent observers for chain_runners.

    """

    chain_runners: TestChain
    skipped: bool
    setup: TestSetup
    teardown: TestTeardown
    watchers: TestWatchers[Driver]
