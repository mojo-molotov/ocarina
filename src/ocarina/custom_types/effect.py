"""Effect types for explicit side-effect management and delayed execution.

This module defines types for side-effecting functions, enabling inversion
of control. Effects are functions that perform side effects (I/O, mutations,
logging) but return nothing.

The Effect pattern provides:
- Explicit side effects in function signatures
- Delayed execution (effects are values until called)
- Composability (effects can be combined and passed around)
- Testability (effects can be mocked or replaced)

Traditional vs Effect pattern:
    Traditional (immediate):
        >>> def save_file(path: str) -> None:
        ...     with open(path, 'w') as f:  # Executes NOW
        ...         f.write(data)

    Effect pattern (delayed):
        >>> def save_file(path: str) -> Effect:
        ...     return lambda: open(path, 'w').write(data)  # Captured
        ...
        >>> effect = save_file("file.txt")  # Not executed yet
        >>> effect()  # Execute when ready

Example:
    >>> # Single effect
    >>> def log_message(msg: str) -> Effect:
    ...     return lambda: print(msg)
    ...
    >>> # Multiple effects
    >>> def cleanup_resources() -> Effects:
    ...     return (lambda: db.close(), lambda: os.remove("/tmp/file"))
    ...
    >>> for effect in cleanup_resources():
    ...     effect()

"""

from collections.abc import Callable

type Effect = Callable[[], None]
"""A side-effecting function with no arguments and no return value.

Represents a deferred side effect captured in a closure. Makes side effects
explicit, composable, and testable.

Common use cases:
- Cleanup/disposal (close files, quit drivers)
- Logging (write logs, send metrics)
- I/O operations (save files, send requests)
- State mutations (update globals, modify resources)

Example:
    >>> # Cleanup effect
    >>> def create_cleanup(driver: WebDriver) -> Effect:
    ...     return lambda: suppress(Exception)(driver.quit)()
    ...
    >>> # Effect composition
    >>> def chain(first: Effect, second: Effect) -> Effect:
    ...     return lambda: (first(), second())

Note:
    Effects should handle errors gracefully, especially cleanup effects
    called in finally blocks.

See Also:
    - BuiltSeleniumWebDriver: Uses Effect for driver cleanup
    - Effects: For multiple effects
"""

type Effects = tuple[Effect, ...]
"""Immutable collection of side-effecting functions.

A tuple of Effect functions representing multiple related side effects
(e.g., cleanup steps, initialization actions).

Benefits:
- Immutability (can't modify after creation)
- Order preservation (execute in defined sequence)
- Type safety (all elements guaranteed to be Effect)

Example:
    >>> # Multiple cleanup effects
    >>> def create_cleanup(driver: WebDriver, temp: str) -> Effects:
    ...     return (lambda: driver.quit(), lambda: os.remove(temp))
    ...
    >>> # Sequential execution with error handling
    >>> for effect in create_cleanup(driver, "/tmp/test"):
    ...     with suppress(Exception):
    ...         effect()
    ...
    >>> # Parallel execution
    >>> from concurrent.futures import ThreadPoolExecutor
    >>> with ThreadPoolExecutor() as executor:
    ...     list(executor.map(lambda e: e(), effects))

See Also:
    - Effect: Single effect type
"""
