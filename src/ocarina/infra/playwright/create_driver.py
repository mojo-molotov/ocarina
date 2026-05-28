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


def create_playwright_driver(
    *,
    browser: SupportedPlaywrightBrowser,
    headless: bool,
    wait_timeout: int,
    profile_path: str | None = None,
    tmp_dir_prefix: str = ".playwright_profile_",
) -> BuiltPlaywrightDriver:
    """Create a PlaywrightDriver wrapped in a BuiltWebDriver tuple.

    Note:
        Playwright ships its own browser binaries (run ``playwright install``),
        so there is no driver-path argument. The browser always runs through a
        persistent context whose user-data-dir is a managed temp directory,
        optionally seeded from ``profile_path``; it is removed on disposal.

    """
    validate(browser, name="browser").assert_that(
        is_in(_SUPPORTED_BROWSERS)
    ).execute().raise_if_invalid()

    return DriverBuilder(
        build_driver=lambda user_data_dir: PlaywrightDriver(
            browser=browser,
            headless=headless,
            wait_timeout=wait_timeout,
            user_data_dir=user_data_dir,
        ),
        profile_path=profile_path,
        tmp_dir_prefix=tmp_dir_prefix,
    ).build()
