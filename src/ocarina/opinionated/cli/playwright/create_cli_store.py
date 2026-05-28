"""CLI store for Playwright.

Mirrors the Selenium CLI store, minus the WebDriver-binary concerns: Playwright
ships its own browsers (``playwright install``), so there is no ``--driver-path``,
and the same three engines (chromium/firefox/webkit) are available on every
platform.
"""

from typing import TYPE_CHECKING, Literal

from ocarina.dsl.invariants.assertions import (
    is_dir,
    is_less_than_or_equal_to,
    is_none,
    is_not_zero,
    is_positive,
)
from ocarina.opinionated.cli.builder import CliArg, CliBuilder
from ocarina.opinionated.cli.phantoms import phantom_validate
from ocarina.opinionated.cli.store import CliStore, field
from ocarina.opinionated.consts.loggers_choices import LOGGERS_CHOICES

if TYPE_CHECKING:
    from argparse import Namespace

    from ocarina.custom_types.effect import Effect
    from ocarina.custom_types.playwright.supported_browsers import (
        SupportedPlaywrightBrowser,
    )
    from ocarina.opinionated.loggers.custom_types.supported_loggers import (
        SupportedLogger,
    )

type PlaywrightCliStoreKeys = Literal[
    "profile_path",
    "browser",
    "headless",
    "workers",
    "logger",
    "wait_timeout",
    "only",
    "exclude",
]

_DEFAULT_WORKERS_AMOUNT = 5
_DEFAULT_LOGGER: SupportedLogger = "terminal+file"
_DEFAULT_BROWSER_AUTOMATION_TIMEOUT = 10
_MAX_BROWSER_AUTOMATION_TIMEOUT = 60

_BROWSER_CHOICES: list[SupportedPlaywrightBrowser] = ["chromium", "firefox", "webkit"]


def _create_validate_only_exclude_mutex_effect(ns: Namespace) -> Effect:
    def _validate() -> None:
        if ns.only and ns.exclude:
            msg = "--only and --exclude cannot be used together"
            raise ValueError(msg)

    return _validate


def _create_store() -> CliStore[PlaywrightCliStoreKeys]:
    return CliStore(
        fields={
            "profile_path": field(
                validate=lambda chain: chain.assert_that(
                    is_none, msg="Maybe you could omit --profile-path"
                ).otherwise(
                    is_dir, msg="--profile-path should be a path to a directory"
                )
            ),
            "browser": field(validate=phantom_validate),
            "headless": field(validate=phantom_validate),
            "workers": field(
                validate=lambda chain: chain.assert_that(
                    is_positive, msg="--workers should be a positive value"
                ).assert_that(is_not_zero, msg="--workers should not be zero")
            ),
            "logger": field(validate=phantom_validate),
            "wait_timeout": field(
                validate=lambda chain: (
                    chain.assert_that(
                        is_less_than_or_equal_to(_MAX_BROWSER_AUTOMATION_TIMEOUT),
                        msg=(
                            "--wait-timeout maximum is:"
                            " "
                            f"{_MAX_BROWSER_AUTOMATION_TIMEOUT}"
                        ),
                    )
                    .assert_that(
                        is_positive, msg="--wait-timeout should be a positive value"
                    )
                    .assert_that(is_not_zero, msg="--wait-timeout should not be zero")
                )
            ),
            "only": field(validate=phantom_validate),
            "exclude": field(validate=phantom_validate),
        }
    )


def _create_cli(store: CliStore[PlaywrightCliStoreKeys]) -> CliBuilder:
    return CliBuilder(
        args=[
            CliArg(
                "--profile-path",
                type=str,
                default=None,
                help="Path to the browser profile directory",
            ),
            CliArg(
                "--browser",
                type=str,
                default=None,
                choices=_BROWSER_CHOICES,
                required=True,
                help="Browser engine to use",
            ),
            CliArg(
                "--not-headless",
                action="store_true",
                help="Runs the browser with a graphical interface",
            ),
            CliArg(
                "--workers",
                type=int,
                default=_DEFAULT_WORKERS_AMOUNT,
                help="Amount of workers to use",
            ),
            CliArg(
                "--logger",
                type=str,
                default=_DEFAULT_LOGGER,
                choices=LOGGERS_CHOICES,
                help="Logger to use",
            ),
            CliArg(
                "--wait-timeout",
                type=int,
                default=_DEFAULT_BROWSER_AUTOMATION_TIMEOUT,
                help=(
                    "Default timeout in seconds for browser automation waits"
                    ", "
                    f"max: {_MAX_BROWSER_AUTOMATION_TIMEOUT}"
                ),
            ),
            CliArg(
                "--only",
                nargs="+",
                default=[],
                metavar="ID",
                help="Run only tests whose test_id is in this list",
            ),
            CliArg(
                "--exclude",
                nargs="+",
                default=[],
                metavar="ID",
                help="Skip tests whose test_id is in this list",
            ),
        ],
        effects_factory=lambda ns: (
            lambda: store.set("profile_path", ns.profile_path),
            lambda: store.set("browser", ns.browser),
            lambda: store.set("headless", not ns.not_headless),
            lambda: store.set("workers", ns.workers),
            lambda: store.set("logger", ns.logger),
            lambda: store.set("wait_timeout", ns.wait_timeout),
            lambda: store.set("only", tuple(ns.only)),
            lambda: store.set("exclude", tuple(ns.exclude)),
            _create_validate_only_exclude_mutex_effect(ns),
        ),
    )


def create_playwright_cli_store() -> CliStore[PlaywrightCliStoreKeys]:
    """Create a CLI store for Playwright."""
    store = _create_store()
    cli = _create_cli(store)
    cli.parse()
    return store


def create_playwright_auto_cli_store() -> CliStore[PlaywrightCliStoreKeys]:
    """Create a CLI store for Playwright.

    Playwright's engines are platform-independent, so this is an alias of
    :func:`create_playwright_cli_store`, provided for naming parity with the
    Selenium launcher.
    """
    return create_playwright_cli_store()
