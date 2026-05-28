"""Per-method default-timeout override for Playwright page objects.

``with_timeout`` is a method decorator — a pre/post hook in the spirit of a Ruby
``alias_method`` wrapper — that temporarily changes the page's default auto-wait
timeout for the duration of one POM method, then restores the driver's
configured default. It does not touch the method body.

Why a decorator (and why this is safe)
---------------------------------------
Playwright already supports per-call ``timeout=`` on every locator action, so
most edge cases are handled at the call site without any global change. This
decorator exists for the case where you want a *whole* method to run under a
different default without threading ``timeout=`` through every call.

The override and the restore are marshalled onto the driver's single owner
thread (see :class:`~ocarina.infra.playwright.driver.PlaywrightDriver`), and the
page has exactly one owner — Ocarina's Playwright watchers are driver-free, so
nothing else can drive the page concurrently. The change therefore cannot
interleave with other page work between override and restore. Each test owns its
own driver, so a per-method override never leaks across parallel workers. The
restore runs in a ``finally`` block, so it survives method failures.

Placement: ONLY on POM methods whose class exposes ``self._driver: PlaywrightDriver``.
Do not use it anywhere else.

Example:
    >>> class CheckoutPage(POMBase):
    ...     def __init__(self, driver: PlaywrightDriver) -> None:
    ...         self._driver = driver
    ...
    ...     @with_timeout(30)  # this slow step gets 30s; the rest keep the default
    ...     def wait_for_payment_redirect(self) -> "CheckoutPage":
    ...         self._driver.submit(lambda page: page.wait_for_url("**/receipt"))
    ...         return self

"""

import functools
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from collections.abc import Callable

    from ocarina.infra.playwright.driver import PlaywrightDriver


def with_timeout(seconds: float) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """Wrap a POM method so it runs under a temporary page default timeout.

    Args:
        seconds: Default timeout to apply for the duration of the method.

    Returns:
        A decorator that overrides the timeout before the call and restores
        the driver's configured default afterwards (even on failure).

    """

    def decorate(method: Callable[..., Any]) -> Callable[..., Any]:
        @functools.wraps(method)
        def wrapper(self: Any, *args: Any, **kwargs: Any) -> Any:  # noqa: ANN401
            driver: PlaywrightDriver = self._driver
            driver.set_default_timeout(int(seconds * 1000))
            try:
                return method(self, *args, **kwargs)
            finally:
                driver.reset_default_timeout()

        return wrapper

    return decorate
