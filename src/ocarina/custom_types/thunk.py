"""Thunk type for lazy evaluation.

A Thunk is a parameterless function that returns a value when called.
Used to defer expensive computations until needed.

Key distinction:
    - Thunk[T]: Returns value (computation)
    - Effect: Returns None (side effect)

Example:
    >>> # Lazy evaluation
    >>> lazy = lambda: expensive_computation()  # Not executed
    >>> result = lazy()  # Executed now

"""

from collections.abc import Callable

type Thunk[T] = Callable[[], T]
