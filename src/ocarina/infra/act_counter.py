"""Steps counter ABC."""

from abc import abstractmethod
from typing import Protocol, runtime_checkable


@runtime_checkable
class ActCounter(Protocol):
    """Tracks act() call count across a test execution."""

    @abstractmethod
    def incr_act_call_count(self) -> None:
        """Increment count."""
        raise NotImplementedError  # pragma: no cover

    @abstractmethod
    def reset(self) -> None:
        """Reset counter to zero."""
        raise NotImplementedError  # pragma: no cover

    @abstractmethod
    def get(self) -> int:
        """Return current count."""
        raise NotImplementedError  # pragma: no cover
