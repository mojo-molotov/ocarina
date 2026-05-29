"""Create a Watcher bound to Ocarina's PlaywrightDriver.

Important — Playwright watchers must be *driver-free*.

A Watcher polls in its own daemon thread, separate from the test chain. With
Playwright's sync API the page is owned by a single thread, so a watcher must
not drive the page. Use Playwright watchers for out-of-page signals only:
external state, logs, a Redis flag, a clock, etc. For page assertions, keep them
inside the test chain.
"""

from typing import TYPE_CHECKING

from ocarina.dsl.testing.watcher import Watcher

if TYPE_CHECKING:
    from collections.abc import Callable

    from ocarina.infra.playwright.driver import PlaywrightDriver

type PlaywrightWatcher = Watcher[PlaywrightDriver]


def create_playwright_watcher(
    *,
    callback: Callable[[PlaywrightWatcher], None],
    name: str,
    poll_interval: float | None = None,
) -> PlaywrightWatcher:
    """Create a driver-free Watcher for Playwright (see module docstring)."""
    return Watcher(
        callback=callback,
        name=name,
        poll_interval=poll_interval,
    )
