"""Side-effecting callables with no arguments and no return value."""

from collections.abc import Callable

type Effect = Callable[[], None]
type Effects = tuple[Effect, ...]
