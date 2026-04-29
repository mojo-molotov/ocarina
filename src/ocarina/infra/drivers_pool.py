"""Generic driver pool with concurrency control via semaphore.

Drivers are never reused — each acquire() disposes after use (clean state).
warmup() pre-fills the pool; acquire() creates on demand if pool is empty.

Safety guarantees:
- No semaphore leaks
- Warmup cannot stall silently
- Stuck warmup is detected via progress watchdog
"""

import threading
import time
from contextlib import contextmanager, suppress
from queue import Empty, Queue
from threading import Semaphore
from typing import TYPE_CHECKING, final

if TYPE_CHECKING:
    from collections.abc import Iterator

    from ocarina.custom_types.built_web_driver import BuiltWebDriver
    from ocarina.custom_types.thunk import Thunk


class WarmupTimeoutError(Exception):
    """Raised when warmup is blocked (mostly some macOS edge cases)."""


@final
class WebDriversPool[Driver]:
    """Thread-safe driver pool. Max concurrency = max_size (semaphore-controlled)."""

    def __init__(
        self,
        create_driver: Thunk[BuiltWebDriver[Driver]],
        max_size: int,
        warmup_timeout: float | None = None,
    ) -> None:
        """Initialize the pool.

        Args:
            create_driver: Factory returning (driver, dispose) tuple.
            max_size: Maximum concurrent drivers allowed.
            warmup_timeout: Seconds without progress before warmup is aborted.

        """
        self._create_driver = create_driver
        self._pool: Queue[BuiltWebDriver[Driver]] = Queue(max_size)
        self._semaphore = Semaphore(max_size)
        self._warmup_timeout = (
            warmup_timeout
            if warmup_timeout is not None and warmup_timeout > 0.1  # noqa: PLR2004
            else 60.0 * 5
        )

    @contextmanager
    def acquire(self) -> Iterator[Driver]:
        """Yield a driver. Blocks if max_size drivers are in use."""
        try:
            driver, dispose = self._pool.get_nowait()
        except Empty:
            self._semaphore.acquire()
            try:
                driver, dispose = self._create_driver()
            except Exception:
                self._semaphore.release()
                raise

        try:
            yield driver
        finally:
            with suppress(Exception):
                dispose()
            self._semaphore.release()

    def warmup(self) -> None:
        """Fully initialize the driver pool, avoiding cold-start latency.

        Raises:
            WarmupTimeoutError: If no progress is detected.

        """
        progress = {"count": 0}
        lock = threading.Lock()
        stop_event = threading.Event()

        def worker() -> None:
            while not self._pool.full() and not stop_event.is_set():
                if not self._semaphore.acquire(blocking=False):
                    break

                try:
                    driver, dispose = self._create_driver()
                    self._pool.put((driver, dispose))

                    with lock:
                        progress["count"] += 1

                except Exception:  # noqa: BLE001
                    self._semaphore.release()
                    break

        t = threading.Thread(target=worker, daemon=True)
        t.start()

        start_global = time.monotonic()
        last_progress = 0

        while t.is_alive():
            time.sleep(0.5)

            with lock:
                current = progress["count"]

            if current != last_progress:
                last_progress = current
                start_global = time.monotonic()

            if time.monotonic() - start_global > self._warmup_timeout:
                stop_event.set()
                msg = (
                    "Warmup stalled (no progress detected)."
                    " "
                    "Some browser processes may still be running."
                    " "
                    "Please check your system (Activity Monitor / Task Manager / Dock)"
                    " "
                    "and close any remaining browser instances."
                )
                self.shutdown()
                raise WarmupTimeoutError(msg)

        t.join()

    def shutdown(self) -> None:
        """Dispose pre-created drivers in the pool. Acquired drivers unaffected."""
        while not self._pool.empty():
            _, dispose = self._pool.get_nowait()
            with suppress(Exception):
                dispose()
            self._semaphore.release()
