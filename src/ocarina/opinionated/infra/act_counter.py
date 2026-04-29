"""ActCounter implementation proposal for TestSuites."""

from threading import local
from typing import Final

from ocarina.infra.act_counter import ActCounter as _ActCounter

_thread_local = local()
_COUNTER_KEY: Final[str] = "ocarina_counter"


class ActCounter(_ActCounter):
    """Tracks act() call count across a test execution."""

    def get(self) -> int:
        """Return current count."""
        return getattr(_thread_local, _COUNTER_KEY, 0)

    def reset(self) -> None:
        """Reset counter to zero."""
        setattr(_thread_local, _COUNTER_KEY, 0)

    def incr_act_call_count(self) -> None:
        """Increment counter."""
        if not hasattr(_thread_local, _COUNTER_KEY):
            self.reset()
        setattr(_thread_local, _COUNTER_KEY, getattr(_thread_local, _COUNTER_KEY) + 1)
