# ruff: noqa: D102
"""Combined loggers: print + files."""

from typing import TYPE_CHECKING, Self, final

from ocarina.ports.ilogger import ILogger

if TYPE_CHECKING:
    from ocarina.custom_types.thunk import Thunk
    from ocarina.opinionated.loggers.file_logger import FileLogger
    from ocarina.opinionated.loggers.print_logger import PrintLogger


@final
class PrintAndFileLogger(ILogger):
    """Combinate loggers: PrintLogger + FileLogger."""

    def __init__(self, print_logger: PrintLogger, file_logger: FileLogger) -> None:
        """Initialize loggers."""
        self._print_logger = print_logger
        self._file_logger = file_logger

    def set_prefix(self, prefix_thunk: Thunk[str]) -> Self:
        self._print_logger.set_prefix(prefix_thunk)
        self._file_logger.set_prefix(prefix_thunk)
        return self

    def set_domain_taxonomy(self, taxonomy: tuple[str, ...]) -> Self:
        self._print_logger.set_domain_taxonomy(taxonomy)
        self._file_logger.set_domain_taxonomy(taxonomy)
        return self

    def raw(self, *args, **kwargs) -> None:
        self._print_logger.raw(*args, **kwargs)
        self._file_logger.raw(*args, **kwargs)

    def critical(self, msg: str, *args, **kwargs) -> None:
        self._print_logger.critical(msg, *args, **kwargs)
        self._file_logger.critical(msg, *args, **kwargs)

    def error(self, msg: str, *args, **kwargs) -> None:
        self._print_logger.error(msg, *args, **kwargs)
        self._file_logger.error(msg, *args, **kwargs)

    def warning(self, msg: str, *args, **kwargs) -> None:
        self._print_logger.warning(msg, *args, **kwargs)
        self._file_logger.warning(msg, *args, **kwargs)

    def info(self, msg: str, *args, **kwargs) -> None:
        self._print_logger.info(msg, *args, **kwargs)
        self._file_logger.info(msg, *args, **kwargs)

    def debug(self, msg: str, *args, **kwargs) -> None:
        self._print_logger.debug(msg, *args, **kwargs)
        self._file_logger.debug(msg, *args, **kwargs)

    def test_name(self, msg: str, *args, **kwargs) -> None:
        self._print_logger.test_name(msg, *args, **kwargs)
        self._file_logger.test_name(msg, *args, **kwargs)

    def success(self, msg: str, *args, **kwargs) -> None:
        self._print_logger.success(msg, *args, **kwargs)
        self._file_logger.success(msg, *args, **kwargs)

    def exception(self, msg: str, *args, **kwargs) -> None:
        self._print_logger.exception(msg, *args, **kwargs)
        self._file_logger.exception(msg, *args, **kwargs)

    def cleanup(self) -> None:
        self._print_logger.cleanup()
        self._file_logger.cleanup()
