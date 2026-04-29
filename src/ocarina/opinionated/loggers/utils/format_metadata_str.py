"""Functions for formatting metadata blocks."""

from datetime import UTC, datetime
from threading import current_thread
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ocarina.custom_types.thunk import Thunk


def _format_metadata_str(*, namespace: str, metadata: str) -> str:
    """Generate and format a metadata block."""
    return "[" + namespace + "::" + metadata + "]"


def format_utc_date_metadata_str() -> str:
    """Generate and format the UTC date metadata block."""
    return _format_metadata_str(
        namespace="UTC_DATE",
        metadata=datetime.now(UTC).isoformat(),
    )


def format_current_thread_metadata_str() -> str:
    """Generate and format the current thread metadata block."""
    return _format_metadata_str(namespace="THREAD", metadata=current_thread().name)


def concat_metadata(*formatters: Thunk[str]) -> str:
    """Concatenate the results of multiple metadata formatters."""
    return "".join(f() for f in formatters)
