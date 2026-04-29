"""Logger with files generation effects."""

from contextlib import suppress
from typing import TYPE_CHECKING, final

if TYPE_CHECKING:
    from pathlib import Path

    from ocarina.custom_types.supports_write import SupportsWrite

from ocarina.opinionated.loggers.print_logger import PrintLogger


@final
class FileLogger(PrintLogger):
    """Log with files generation effects."""

    def __init__(
        self,
        *,
        base_dir: Path,
        with_flush_effect: bool = True,
        with_fallback_on_print_logger_when_no_taxonomy_effect: bool = True,
    ) -> None:
        """Initialize the FileLogger.

        Args:
            base_dir: Root directory where log files are written.
            with_flush_effect: Print log file content to stdout on cleanup.
            with_fallback_on_print_logger_when_no_taxonomy_effect: Fall back to
                PrintLogger when no taxonomy is set.

        """
        self._base_dir = base_dir
        self._with_flush_effect = with_flush_effect
        self._with_fallback_on_print_logger_when_no_taxonomy_effect = (
            with_fallback_on_print_logger_when_no_taxonomy_effect
        )
        super().__init__()

    def _has_taxonomy(self) -> bool:
        return any(part for part in self._domain_taxonomy)

    @property
    def _log_file_path(self) -> Path:
        if len(self._domain_taxonomy) == 1:
            folder_path = self._base_dir
            file_name = f"{self._domain_taxonomy[0]}.log"
        else:
            folder_path = self._base_dir.joinpath(*self._domain_taxonomy[:-1])
            file_name = f"{self._domain_taxonomy[-1]}.log"

        folder_path.mkdir(parents=True, exist_ok=True)
        return folder_path / file_name

    def _print_log(
        self,
        prefix: str,
        msg: str,
        *args,
        exc: BaseException | None = None,
        stream: SupportsWrite[str],
    ) -> None:
        formatted_msg = msg % args if args else msg

        output = " ".join(
            part
            for part in [
                self._prefix_thunk(),
                prefix,
                formatted_msg,
            ]
            if part
        )
        self._write_log_hook(output, exc, stream)

    def _write_log_hook(
        self,
        output: str,
        exc: BaseException | None,
        stream: SupportsWrite[str],
    ) -> None:
        if self._has_taxonomy():
            log_file_path = self._log_file_path
            with log_file_path.open("a", encoding="utf-8") as f:
                self._flush_log(output, exc, f)
        elif self._with_fallback_on_print_logger_when_no_taxonomy_effect:
            super()._write_log_hook(output, exc, stream)

    def cleanup(self) -> None:
        """Remove the log file linked to the taxonomy, flushing it first."""
        if self._has_taxonomy():
            log_file_path = self._log_file_path

            if log_file_path.exists():
                if self._with_flush_effect:
                    print_logger = PrintLogger().set_domain_taxonomy(
                        self._domain_taxonomy
                    )
                    print_logger.raw()
                    print_logger.info("Flush:")
                    with log_file_path.open("r", encoding="utf-8") as f:
                        while chunk := f.read(1024):
                            print_logger.raw(chunk, end="")

                with suppress(Exception):
                    log_file_path.unlink()
