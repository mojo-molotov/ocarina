"""WebDriver paired with its disposal Effect.

The disposal Effect must be fire-and-forget: it has to suppress all exceptions
and never raise — it runs in cleanup paths where raising would mask the
original test failure.
"""

from ocarina.custom_types.effect import Effect

type BuiltWebDriver[Driver] = tuple[Driver, Effect]
