"""Singleton wrapper for a CliStore instance.

Holds a single CliStore for the duration of the runtime.
Intended to be populated once at startup and read from anywhere thereafter.
Subsequent push() calls are silently ignored — the first one wins.

By default TKeys is str — no autocompletion, no mypy validation on keys.
If key safety is needed, create a typed alias in user-land:

Example:
    >>> # lib usage — no key typing
    >>> CliStoreSingleton().push(store)
    >>> CliStoreSingleton().get("workers")

    >>> # user-land — typed alias with autocompletion
    >>> MyCliStoreSingleton = CliStoreSingleton[SeleniumCliStoreKeys]
    >>> MyCliStoreSingleton().push(store)
    >>> MyCliStoreSingleton().get("workers")  # autocompleted + mypy

"""

from threading import Lock
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from ocarina.opinionated.cli.store import CliStore


class _SingletonMeta(type):
    _instances: dict[type, Any] = {}  # noqa: RUF012
    _lock: Lock = Lock()

    def __call__(cls, *args: Any, **kwargs: Any) -> Any:  # noqa: ANN401
        with cls._lock:
            if cls not in cls._instances:
                cls._instances[cls] = super().__call__(*args, **kwargs)
        return cls._instances[cls]


class CliStoreSingleton[TKeys: str = str](metaclass=_SingletonMeta):
    """Singleton holder for a CliStore instance.

    TKeys defaults to str. Pass a Literal type to enable key autocompletion
    and mypy validation — see module docstring for usage.

    Push the store once after CLI parsing. Call get() anywhere in the runtime.
    A second push() is silently ignored — the first one wins.
    A get() before any push() raises RuntimeError.
    """

    _lock: Lock = Lock()

    def __init__(self) -> None:
        """CliStoreSingleton holds the CliStore instance."""
        self._store: CliStore[TKeys] | None = None

    def push(self, store: CliStore[TKeys]) -> None:
        """Store the CliStore instance. Silently ignored if already set.

        Args:
            store: The CliStore to hold for the duration of the runtime.

        """
        with self._lock:
            if self._store is not None:
                return
            self._store = store

    def get(self, k: TKeys) -> Any:  # noqa: ANN401
        """Get a value by key from the stored CliStore.

        Args:
            k: A valid store key. Autocompleted if TKeys is a Literal type.

        Raises:
            RuntimeError: If no store has been pushed yet.

        """
        if self._store is None:
            msg = "No store has been pushed yet. Call push() first."
            raise RuntimeError(msg)
        return self._store.get(k)
