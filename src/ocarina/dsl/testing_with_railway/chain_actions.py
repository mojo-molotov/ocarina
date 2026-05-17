"""Chain actions operator for composing Railway action sequences.

Provides utilities for composing multiple Railway actions into a single
lazy execution unit, solving the "parenthesis hell" problem.

Solution:
    >>> # Flat, readable syntax
    >>> runner = chain_actions(
    ...     action1.failure(h1).success(h2),
    ...     action2.failure(h3).success(h4),
    ...     action3.failure(h5).success(h6)
    ... )
    >>> chain = runner.run()  # Execute when ready

Benefits:
- Lazy evaluation: Build chain without executing
- Flat syntax: No deep nesting
- Automatic short-circuiting: Stops on first failure
- Composability: ChainRunner is a value

Example:
    >>> # Test usage
    ... def test_scenario(driver, logger):
    ...     return [
    ...         chain_actions(
    ...             act(page, step1).failure(log_error).success(log_success),
    ...             act(page, step2).failure(log_error).success(log_success)
    ...         )
    ...     ]

"""

from functools import reduce
from typing import TYPE_CHECKING, final

if TYPE_CHECKING:
    from ocarina.custom_types.thunk import Thunk
    from ocarina.dsl.testing_with_railway.internals.action_chain import (
        ActionChain,
        ActionSuccess,
    )


@final
class ChainRunner[T]:
    """Lazy execution wrapper for Railway action chains.

    Encapsulates a sequence of Railway actions that have been composed
    but not yet executed. Stores a thunk that executes the chain when
    run() is called.

    Example:
        >>> runner = chain_actions(action1, action2)
        >>> chain = runner.run()  # Execute when ready
        >>> if chain.has_failed():
        ...     logger.error("Chain failed")

    """

    def __init__(self, *, thunk: Thunk[ActionChain[T]]) -> None:
        """Initialize with lazy computation."""
        self._thunk = thunk

    def run(self) -> ActionChain[T]:
        """Execute the lazy action chain and return result.

        Returns:
            ActionChain[T] with final state after execution.

        Example:
            >>> chain = runner.run()
            >>> if chain.is_ok():
            ...     logger.success("All succeeded")

        """
        return self._thunk()


def chain_actions[T](
    first: ActionSuccess[T], *rest: ActionSuccess[T]
) -> ChainRunner[T]:
    """Compose multiple configured actions into lazy execution chain.

    Takes ActionSuccess instances (with both handlers configured) and
    composes them into a ChainRunner that executes sequentially with
    automatic short-circuiting on failure.

    Solves "parenthesis hell" by flattening nested .then().execute() chains.

    Execution:
        1. Execute first action with handlers
        2. If failed: short-circuit, return failed chain
        3. If succeeded: chain next action with .then()
        4. Repeat for all actions
        5. Return final chain state

    Args:
        first: First action (with handlers configured).
        *rest: Additional actions in sequence.

    Returns:
        ChainRunner[T] that lazily executes when run() is called.

    Example:
        >>> # With short-circuit
        ... runner = chain_actions(
        ...     failing_action.failure(h1).success(h2),
        ...     never_runs.failure(h3).success(h4)  # Skipped
        ... )
        >>> chain = runner.run()
        >>> assert chain.has_failed()

    Example:
        >>> runner = chain_actions(
        ...     action1.failure(h1).success(h2),
        ...     action2.failure(h3).success(h4)
        ... )
        >>> chain = runner.run()

    """

    def thunk() -> ActionChain[T]:
        """Lazy computation executing the action sequence."""

        def reducer(chain: ActionChain[T], step: ActionSuccess[T]) -> ActionChain[T]:
            """Fold function chaining actions with short-circuit logic."""
            if chain.has_failed():
                return chain

            return (
                chain.then(step.__action__)
                .failure(step.__failure_handler__)
                .success(step.__success_handler__)
                .execute()
            )

        return reduce(reducer, rest, first.execute())

    return ChainRunner(thunk=thunk)
