"""Create a Watcher bound to Ocarina's PlaywrightDriver.

A Watcher polls in its own daemon thread, separate from the test chain. A
Playwright watcher MAY read the page from its callback via
``watcher.driver.submit(...)`` — the call is marshalled onto the driver's owner
thread, so it is safe across threads (no greenlet error, no re-entrant
deadlock). It is not forbidden; it is governed by a convention:

- OBSERVE, do not MUTATE. The watcher polls concurrently with the test chain;
  mutating the page (click/fill) from a watcher corrupts the test's state. This
  holds in every framework, Selenium included — the canonical Selenium watcher
  only reads (is_visible/get_text). Read-only is the user's responsibility.
- Always go through ``submit``; never touch ``page`` directly (it is
  thread-bound to the owner thread).
- Return FLAT data from the lambda (str/bool/bytes); never a live Locator or
  ElementHandle (they are bound to the owner thread).
- Performance caveat: each read serialises on the owner thread alongside the
  test chain's own ``submit`` calls — contention scales with ``poll_interval``.
  Selenium watchers, sharing the driver directly, are freer here.
- ``watcher.report()`` is fine: its screenshot already goes through
  ITakeScreenshot -> submit, so it is marshalled like any other page read.

Example (read-only observation, reported):
    >>> def watch_banner(watcher: PlaywrightWatcher) -> None:
    ...     text = watcher.driver.submit(
    ...         lambda page: page.inner_text("#cookie-banner")
    ...         if page.locator("#cookie-banner").count()
    ...         else ""
    ...     )
    ...     if text and text not in watcher.cache:
    ...         watcher.cache.add(text)
    ...         watcher.report(f"Cookie banner: {text!r}", label="BANNER")
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
    """Create a Watcher for Playwright (observe-only; see module docstring)."""
    return Watcher(
        callback=callback,
        name=name,
        poll_interval=poll_interval,
    )
