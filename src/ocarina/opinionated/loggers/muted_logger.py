# ruff: noqa: D102
"""Muted logger."""

from typing import TYPE_CHECKING, final

from ocarina.ports.ilogger import ILogger

if TYPE_CHECKING:
    from ocarina.custom_types.supports_write import SupportsWrite
    from ocarina.custom_types.thunk import Thunk


@final
class MutedLogger(ILogger):
    """Does nothing."""

    def raw(self, *args, stream: SupportsWrite[str] | None = None, **kwargs) -> None:
        pass

    def critical(self, msg: str, *args, **kwargs) -> None:
        pass

    def error(self, msg: str, *args, **kwargs) -> None:
        pass

    def warning(self, msg: str, *args, **kwargs) -> None:
        pass

    def info(self, msg: str, *args, **kwargs) -> None:
        pass

    def debug(self, msg: str, *args, **kwargs) -> None:
        pass

    def test_name(self, msg: str, *args, **kwargs) -> None:
        pass

    def success(self, msg: str, *args, **kwargs) -> None:
        pass

    def exception(self, msg: str, *args, **kwargs) -> None:
        pass

    def set_prefix(self, prefix_thunk: Thunk[str]) -> MutedLogger:  # noqa: ARG002
        return self

    def set_domain_taxonomy(self, taxonomy: tuple[str, ...]) -> MutedLogger:  # noqa: ARG002
        return self

    def cleanup(self) -> None:
        pass
