"""Factory for creating a default logger based on a supported logger mode."""

import uuid
from pathlib import Path
from threading import Lock
from typing import TYPE_CHECKING

from ocarina.opinionated.loggers.file_logger import FileLogger
from ocarina.opinionated.loggers.muted_logger import MutedLogger
from ocarina.opinionated.loggers.print_and_file_logger import PrintAndFileLogger
from ocarina.opinionated.loggers.print_logger import PrintLogger
from ocarina.opinionated.loggers.utils.format_metadata_str import (
    concat_metadata,
    format_current_thread_metadata_str,
    format_utc_date_metadata_str,
)

if TYPE_CHECKING:
    from ocarina.custom_types.thunk import Thunk
    from ocarina.opinionated.loggers.custom_types.supported_loggers import (
        SupportedLogger,
    )
    from ocarina.ports.ilogger import ILogger

_MAX_ATTEMPTS = 500
_BASE_NAME = ".ocarina_logs"
_resolve_lock = Lock()
_GLOB_DEFAULT_LOG_DIR: Path | None = None


def _do_resolve() -> Path:
    base = Path.cwd() / _BASE_NAME
    if not base.exists():
        return base
    for _ in range(_MAX_ATTEMPTS):  # pragma: no cover
        candidate = Path.cwd() / f"{_BASE_NAME}_{uuid.uuid4().hex[:8]}"
        if not candidate.exists():
            return candidate
    msg = f"Could not find an available log directory after {_MAX_ATTEMPTS} attempts."  # pragma: no cover  # noqa: E501
    raise RuntimeError(msg)  # pragma: no cover


def _resolve_log_dir() -> Path:
    global _GLOB_DEFAULT_LOG_DIR  # noqa: PLW0603
    with _resolve_lock:  # pragma: no cover
        if _GLOB_DEFAULT_LOG_DIR is None:
            _GLOB_DEFAULT_LOG_DIR = _do_resolve()
        return _GLOB_DEFAULT_LOG_DIR


_DEFAULT_LOG_DIR = _resolve_log_dir()


def get_default_log_dir() -> Path:  # pragma: no cover
    """Get the default log directory for this logger."""
    return _DEFAULT_LOG_DIR


def create_matching_logger(
    logger_mode: SupportedLogger,
    base_dir: Path = _DEFAULT_LOG_DIR,
) -> ILogger:
    """Create a logger instance based on the given logger mode.

    Terminal prefix : "[UTC_DATE][THREAD_ID]"
    File prefix     : "[UTC_DATE]"

    Args:
        logger_mode: The logging mode to use.
                     - "mute"          : No output.
                     - "terminal"      : Console with date + thread.
                     - "file"          : Files with date only.
                     - "terminal+file" : Console (date + thread) + Files (date).
                                         Files without auto-flush and without
                                         fallback to PrintLogger.
        base_dir: Root directory where log files are written.
                  Defaults to a fresh directory created for the whole process cycle.

    Returns:
        ILogger: A configured logger instance.

    Example:
        >>> logger = create_matching_logger("terminal+file")
        >>> logger.info("Test started")
        [2025-12-20T10:30:00Z][Thread-1] Test started

        >>> logger = create_matching_logger("mute")
        >>> logger.info("This is not logged")  # no output

        >>> # Custom base_dir
        >>> logger = create_matching_logger("file", base_dir=Path("/var/log/myapp"))

        >>> # Typical usage with CliStoreSingleton
        >>> logger = create_matching_logger(CliStoreSingleton().get("logger"))

    """

    def _terminal_prefix() -> str:
        return concat_metadata(  # pragma: no cover
            format_utc_date_metadata_str, format_current_thread_metadata_str
        )

    def _file_prefix() -> str:
        return format_utc_date_metadata_str()  # pragma: no cover

    dispatchers: dict[SupportedLogger, Thunk[ILogger]] = {
        "mute": lambda: MutedLogger(),  # noqa: PLW0108
        "terminal": lambda: PrintLogger().set_prefix(_terminal_prefix),
        "file": lambda: FileLogger(base_dir=base_dir).set_prefix(_file_prefix),
        "terminal+file": lambda: PrintAndFileLogger(
            PrintLogger().set_prefix(_terminal_prefix),
            FileLogger(
                base_dir=base_dir,
                with_flush_effect=False,
                with_fallback_on_print_logger_when_no_taxonomy_effect=False,
            ).set_prefix(_file_prefix),
        ),
    }

    return dispatchers[logger_mode]()
