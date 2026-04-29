"""Literals union, representing supported loggers."""

from typing import Literal

type SupportedLogger = Literal["mute", "terminal", "file", "terminal+file"]
