"""Take screenshot callable."""

from collections.abc import Callable

from ocarina.ports.ilogger import ILogger

type ITakeScreenshot[Driver] = Callable[[Driver, ILogger, str], None]
