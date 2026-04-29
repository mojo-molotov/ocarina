"""Loggers choices constant."""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ocarina.opinionated.loggers.custom_types.supported_loggers import (
        SupportedLogger,
    )

LOGGERS_CHOICES: list[SupportedLogger] = ["mute", "terminal", "file", "terminal+file"]
