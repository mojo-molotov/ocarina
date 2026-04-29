# ruff: noqa: D102, ARG002
"""Logger using print."""

import sys
import traceback
from typing import TYPE_CHECKING, Self

from ocarina.ports.ilogger import ILogger

if TYPE_CHECKING:
    from ocarina.custom_types.supports_write import SupportsWrite
    from ocarina.custom_types.thunk import Thunk


class PrintLogger(ILogger):
    """Log with print."""

    def __init__(self) -> None:
        """Initialize logger without prefix nor taxonomy."""
        self._prefix_thunk: Thunk[str] = lambda: ""
        self._domain_taxonomy: tuple[str, ...] = ("",)

    def set_prefix(self, prefix_thunk: Thunk[str]) -> Self:
        self._prefix_thunk = prefix_thunk
        return self

    def set_domain_taxonomy(self, taxonomy: tuple[str, ...]) -> Self:
        self._domain_taxonomy = taxonomy
        return self

    def raw(
        self,
        *args,
        stream: SupportsWrite[str] | None = None,
        **kwargs,
    ) -> None:
        if stream is None:
            stream = sys.stdout
        print(*args, file=stream, **kwargs)

    def critical(
        self, msg: str, *args, exc: BaseException | None = None, **kwargs
    ) -> None:
        self._print_log("💥 ", msg, *args, exc=exc, stream=sys.stderr)

    def error(self, msg: str, *args, exc: Exception | None = None, **kwargs) -> None:
        self._print_log("🛑 ", msg, *args, exc=exc, stream=sys.stderr)

    def warning(self, msg: str, *args, exc: Exception | None = None, **kwargs) -> None:
        self._print_log("⚠️ ", msg, *args, exc=exc, stream=sys.stdout)

    def info(self, msg: str, *args, exc: Exception | None = None, **kwargs) -> None:
        self._print_log("ℹ️ ", msg, *args, exc=exc, stream=sys.stdout)  # noqa: RUF001 -> Emoji is intentional.

    def debug(self, msg: str, *args, exc: Exception | None = None, **kwargs) -> None:
        self._print_log("🐞 ", msg, *args, exc=exc, stream=sys.stdout)

    def test_name(
        self, msg: str, *args, exc: Exception | None = None, **kwargs
    ) -> None:
        self._print_log("🧪 ", msg, *args, exc=exc, stream=sys.stdout)

    def success(self, msg: str, *args, exc: Exception | None = None, **kwargs) -> None:
        self._print_log("✅ ", msg, *args, exc=exc, stream=sys.stdout)

    def exception(
        self, msg: str, *args, exc: BaseException | None = None, **kwargs
    ) -> None:
        if exc is None:
            _, exc, _ = sys.exc_info()
        if exc:
            self.critical(msg, *args, exc=exc)
        else:
            self.error(msg, *args, **kwargs)

    def _format_taxonomy(self) -> str:
        parts = [part for part in self._domain_taxonomy if part]

        if not parts:
            return ""

        return "/".join(parts) + " —"

    def _flush_log(
        self, output: str, exc: BaseException | None, stream: SupportsWrite[str]
    ) -> None:
        print(output, file=stream)
        if exc:
            tb_str = "".join(
                traceback.format_exception(type(exc), exc, exc.__traceback__)
            )
            print(tb_str, file=stream)

    def _write_log_hook(
        self,
        output: str,
        exc: BaseException | None,
        stream: SupportsWrite[str],
    ) -> None:
        self._flush_log(output, exc, stream)

    def _print_log(
        self,
        prefix: str,
        msg: str,
        *args,
        exc: BaseException | None = None,
        stream: SupportsWrite[str],
    ) -> None:
        formatted_msg = msg % args if args else msg
        taxonomy = self._format_taxonomy()

        output = " ".join(
            part
            for part in [
                self._prefix_thunk(),
                prefix,
                taxonomy,
                formatted_msg,
            ]
            if part
        )
        self._write_log_hook(output, exc, stream)

    def cleanup(self) -> None:
        pass
