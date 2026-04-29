"""CLI stores for Selenium."""

import atexit
import platform
import shutil
import tempfile
from contextlib import suppress
from pathlib import Path
from typing import TYPE_CHECKING, Literal

from ocarina.dsl.invariants.assertions import (
    is_dir,
    is_file,
    is_less_than_or_equal_to,
    is_none,
    is_not_zero,
    is_positive,
)
from ocarina.dsl.invariants.validate import validate
from ocarina.opinionated.cli.builder import CliArg, CliBuilder
from ocarina.opinionated.cli.phantoms import phantom_validate
from ocarina.opinionated.cli.store import CliStore, field
from ocarina.opinionated.consts.loggers_choices import LOGGERS_CHOICES
from ocarina.opinionated.loggers.create_matching_logger import create_matching_logger

if TYPE_CHECKING:
    from argparse import Namespace

    from ocarina.custom_types.effect import Effect
    from ocarina.custom_types.selenium.supported_browsers import (
        SupportedSeleniumBrowser,
    )
    from ocarina.opinionated.loggers.custom_types.supported_loggers import (
        SupportedLogger,
    )

type SeleniumCliStoreKeys = Literal[
    "driver_path",
    "profile_path",
    "browser",
    "headless",
    "workers",
    "logger",
    "wait_timeout",
    "force_delete_tmp_dirs",
    "only",
    "exclude",
]

_DEFAULT_WORKERS_AMOUNT = 5
_DEFAULT_LOGGER: SupportedLogger = "terminal+file"
_DEFAULT_BROWSER_AUTOMATION_TIMEOUT = 10
_MAX_BROWSER_AUTOMATION_TIMEOUT = 60

_WIN_BROWSER_CHOICES: list[SupportedSeleniumBrowser] = ["chrome", "firefox", "edge"]
_MACOS_BROWSER_CHOICES: list[SupportedSeleniumBrowser] = ["chrome", "firefox", "safari"]
_LINUX_BROWSER_CHOICES: list[SupportedSeleniumBrowser] = ["chrome", "firefox"]


def _create_dont_force_delete_tmp_dirs_effect(  # pragma: no cover
    *, dont_force_delete_tmp_dirs: bool
) -> Effect:
    def _clean_all_webdriver_tmp_dirs() -> None:
        def _process_delete(candidate: Path) -> None:
            log = create_matching_logger("terminal")
            try:
                shutil.rmtree(candidate)
            except Exception as exc:  # noqa: BLE001
                msg = f"Failed to delete Selenium temp directory: {candidate!s} ({exc})"
                log.warning(msg)
            else:
                msg = f"Deleted Selenium temp directory: {candidate!s}"
                log.info(msg)

        tmp_dir = Path(tempfile.gettempdir())
        for candidate in tmp_dir.glob("tmp*"):
            if not candidate.is_dir():
                continue
            with suppress(Exception):
                subdirs = [p.name for p in candidate.iterdir() if p.is_dir()]
                if subdirs == ["webdriver-py-profilecopy"]:
                    _process_delete(candidate)

        for candidate in tmp_dir.glob("rust_mozprofile*"):
            if candidate.is_dir():
                with suppress(Exception):
                    _process_delete(candidate)

    def unwrapped() -> None:
        if not dont_force_delete_tmp_dirs and platform.system() == "Windows":
            atexit.register(_clean_all_webdriver_tmp_dirs)

    return unwrapped


def _create_validate_driver_path(ns: Namespace) -> Effect:
    def _validate_driver_path() -> None:
        if ns.browser != "safari":
            validate(ns.driver_path).assert_that(
                is_file, msg="--driver-path should be a path to a file"
            ).execute().raise_if_invalid()

    return _validate_driver_path


def _create_validate_only_exclude_mutex_effect(ns: Namespace) -> Effect:
    def _validate() -> None:
        if ns.only and ns.exclude:
            msg = "--only and --exclude cannot be used together"
            raise ValueError(msg)

    return _validate


def _create_validate_dependent_args_effect(ns: Namespace) -> Effect:
    def _validate_non_safari() -> None:
        is_unset: dict[str, bool] = {
            "--driver-path": ns.driver_path is None and ns.driver_path != "",
            "--browser": ns.browser is None,
        }

        all_explicit = all(not v for v in is_unset.values())

        if not all_explicit:
            msg = "These parameters must all be specified:\n" + "\n".join(
                f"  • {p}" for p in is_unset
            )
            raise ValueError(msg)

    def _validate_safari() -> None:
        forbidden: dict[str, bool] = {
            "--driver-path": ns.driver_path is not None and ns.driver_path != "",
            "--profile-path": ns.profile_path is not None,
        }

        specified = [k for k, v in forbidden.items() if v]

        if specified:
            msg = (
                "Safari uses the native macOS safaridriver"
                " — these arguments are not supported:\n"
                + "\n".join(f"  • {p}" for p in specified)
            )
            raise ValueError(msg)

    def _validate() -> None:
        browser: SupportedSeleniumBrowser = ns.browser
        if browser == "safari":
            _validate_safari()
        else:
            _validate_non_safari()

    return _validate


def _create_store() -> CliStore[SeleniumCliStoreKeys]:
    return CliStore(
        fields={
            "driver_path": field(validate=phantom_validate),
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
            "force_delete_tmp_dirs": field(validate=phantom_validate),
            "only": field(validate=phantom_validate),
            "exclude": field(validate=phantom_validate),
        }
    )


def _create_cli(
    store: CliStore[SeleniumCliStoreKeys],
    browser_choices: list[SupportedSeleniumBrowser],
) -> CliBuilder:
    return CliBuilder(
        args=[
            CliArg(
                "--driver-path",
                type=str,
                default="",
                help="Path to the Selenium driver",
            ),
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
                choices=browser_choices,
                help="Path to the browser profile directory",
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
                    "Global timeout in seconds for browser automation waits"
                    ", "
                    f"max: {_MAX_BROWSER_AUTOMATION_TIMEOUT}"
                ),
            ),
            CliArg(
                "--dont-force-delete-tmp-dirs",
                action="store_true",
                help="Disable forced Selenium and Geckodriver temp files cleanup",
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
            lambda: store.set("driver_path", ns.driver_path),
            lambda: store.set("profile_path", ns.profile_path),
            lambda: store.set("browser", ns.browser),
            lambda: store.set("headless", not ns.not_headless),
            lambda: store.set("workers", ns.workers),
            lambda: store.set("logger", ns.logger),
            lambda: store.set("wait_timeout", ns.wait_timeout),
            lambda: store.set(
                "force_delete_tmp_dirs", not ns.dont_force_delete_tmp_dirs
            ),
            lambda: store.set("only", tuple(ns.only)),
            lambda: store.set("exclude", tuple(ns.exclude)),
            _create_validate_only_exclude_mutex_effect(ns),
            _create_validate_dependent_args_effect(ns),
            _create_validate_driver_path(ns),
            _create_dont_force_delete_tmp_dirs_effect(
                dont_force_delete_tmp_dirs=ns.dont_force_delete_tmp_dirs
            ),
        ),
    )


def _create_selenium_cli_store(
    browser_choices: list[SupportedSeleniumBrowser],
) -> CliStore[SeleniumCliStoreKeys]:
    store = _create_store()
    cli = _create_cli(store, browser_choices)
    cli.parse()
    return store


def create_selenium_win_cli_store() -> CliStore[SeleniumCliStoreKeys]:
    """Create a CLI store for Selenium, on Windows."""
    return _create_selenium_cli_store(_WIN_BROWSER_CHOICES)


def create_selenium_macos_cli_store() -> CliStore[SeleniumCliStoreKeys]:
    """Create a CLI store for Selenium, on macOS."""
    return _create_selenium_cli_store(_MACOS_BROWSER_CHOICES)


def create_selenium_linux_cli_store() -> CliStore[SeleniumCliStoreKeys]:
    """Create a CLI store for Selenium, on Linux."""
    return _create_selenium_cli_store(_LINUX_BROWSER_CHOICES)


def create_selenium_auto_cli_store() -> CliStore[SeleniumCliStoreKeys]:
    """Create a CLI store for Selenium, auto-detecting the current platform."""
    match platform.system():
        case "Windows":
            return create_selenium_win_cli_store()
        case "Darwin":
            return create_selenium_macos_cli_store()
        case "Linux":
            return create_selenium_linux_cli_store()
        case other:
            msg = f"Unsupported platform: {other}"
            raise RuntimeError(msg)
