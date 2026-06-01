"""Playwright driver builder."""

from typing import TYPE_CHECKING

from ocarina.dsl.invariants.assertions import is_in
from ocarina.dsl.invariants.validate import validate
from ocarina.infra.driver_builder import DriverBuilder
from ocarina.infra.playwright.driver import PlaywrightDriver

if TYPE_CHECKING:
    from ocarina.custom_types.playwright.built_web_driver import BuiltPlaywrightDriver
    from ocarina.custom_types.playwright.supported_browsers import (
        SupportedPlaywrightBrowser,
    )

_SUPPORTED_BROWSERS: tuple[SupportedPlaywrightBrowser, ...] = (
    "chromium",
    "firefox",
    "webkit",
)


def create_playwright_driver(  # noqa: PLR0913
    *,
    browser: SupportedPlaywrightBrowser,
    headless: bool,
    wait_timeout: int,
    profile_path: str | None = None,
    tmp_dir_prefix: str = ".playwright_profile_",
    record_video_dir: str | None = None,
    trace_dir: str | None = None,
    call_timeout: float | None = None,
) -> BuiltPlaywrightDriver:
    """Create a PlaywrightDriver wrapped in a BuiltWebDriver tuple.

    Note:
        Playwright ships its own browser binaries (run ``playwright install``),
        so there is no driver-path argument. The browser always runs through a
        persistent context whose user-data-dir is a managed temp directory,
        optionally seeded from ``profile_path``; it is removed on disposal.

        ``record_video_dir`` and ``trace_dir`` are opt-in (off by default): set
        them to capture a session video and/or a Playwright trace
        (``trace_<id>.zip``, open with ``playwright show-trace``). Both are
        written to disk when the driver is disposed, kept there, and accumulate
        across runs — nothing is overwritten or auto-cleaned.

        ``call_timeout`` (seconds) is the liveness ceiling for a single
        marshalled call before the driver is declared dead — a generous
        last-resort bound on a wedged owner thread, not a per-operation
        deadline, and independent of ``wait_timeout``. Leave it ``None`` to use
        ``PlaywrightDriver``'s default. It must sit above the slowest legitimate
        single call (e.g. a long humanized fill or a large per-call
        ``timeout=``); lower it only for faster dead-driver recovery.

    """
    validate(browser, name="browser").assert_that(
        is_in(_SUPPORTED_BROWSERS)
    ).execute().raise_if_invalid()

    extra_kwargs = (
        {} if call_timeout is None else {"call_timeout": call_timeout}
    )

    return DriverBuilder(
        build_driver=lambda user_data_dir: PlaywrightDriver(
            browser=browser,
            headless=headless,
            wait_timeout=wait_timeout,
            user_data_dir=user_data_dir,
            record_video_dir=record_video_dir,
            trace_dir=trace_dir,
            **extra_kwargs,
        ),
        profile_path=profile_path,
        tmp_dir_prefix=tmp_dir_prefix,
    ).build()
