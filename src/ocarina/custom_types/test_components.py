"""Test components - test features types."""

from collections.abc import Sequence
from typing import Any

from ocarina.custom_types.effect import Effect
from ocarina.dsl.testing.watcher import Watcher
from ocarina.dsl.testing_with_railway.chain_actions import ChainRunner

type TestChain = Sequence[ChainRunner[Any]]
type TestSetup = Effect | None
type TestTeardown = Effect | None
type TestWatchers[Driver] = Sequence[Watcher[Driver]] | None
