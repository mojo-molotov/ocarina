"""Railway Oriented Programming implementation for action chains.

Implements the Railway Oriented Programming (ROP) pattern for building
resilient, composable action chains with explicit error handling.

The pattern provides:
- Type-safe success/failure representation (Result[T] = Ok[T] | Fail)
- Builder pattern for configuring error and success handlers
- Automatic short-circuiting on failure (railway switches tracks)
- Composable action chains with .then() combinator

Railway metaphor:
    Code as railway track with two rails:
    - Success rail (top): Actions execute normally → Ok results
    - Failure rail (bottom): Action failed → Fail results

    When an action fails, the train switches to the failure rail and
    stays there (short-circuits). Subsequent actions become no-ops.

Core types:
    Result[T]     → Ok[T] | Fail (from railway.result)
    Action[T]     → Thunk producing Result[T]
    ActionChain   → Railway track with current position

State machine:
    ActionStart → .failure() → ActionFailure → .success() → ActionSuccess
                                                            → .execute() → ActionChain
                                                                          → .then()
                                                                          → ...

Example:
    >>> def risky_action() -> Result[int]:
    ...     if random.random() > 0.5:
    ...         return Ok(42)
    ...     return Fail(Exception("Bad luck"))
    ...
    >>> chain = (
    ...     ActionStart(risky_action)
    ...     .failure(lambda e: logger.error(f"Failed: {e}"))
    ...     .success(lambda: logger.success("Succeeded"))
    ...     .execute()
    ... )
    ...
    >>> if chain.has_failed():
    ...     logger.warning("On failure rail")

"""

from collections.abc import Callable
from typing import final

from ocarina.custom_types.effect import Effect
from ocarina.custom_types.thunk import Thunk
from ocarina.railway.result import Result, is_fail

type Action[T] = Thunk[Result[T]]
"""Deferred computation producing a Result when called.

Signature: () -> Result[T]

Example:
    >>> def create_action() -> Action[int]:
    ...     return lambda: Ok(expensive_computation())
"""

type FailureHandler = Callable[[Exception], None]
"""Handler for failures, receives the error.

Used for logging, screenshots, cleanup, metrics.

Example:
    >>> def handle_error(exc: Exception) -> None:
    ...     logger.error(f"Failed: {exc}", exc=exc)
    ...     take_screenshot(driver, "ERROR")
"""

type SuccHandler = Effect
"""Handler for successes (Effect).

Used for logging, screenshots, metrics.

Example:
    >>> def handle_success() -> None:
    ...     logger.success("Action succeeded")
"""


@final
class ActionStart[T]:
    """Initial action chain builder state, awaiting failure handler.

    Entry point for building an action chain.

    Example:
        >>> ActionStart(action).failure(handle_error).success(handle_success).execute()

    """

    def __init__(self, action: Action[T]) -> None:
        """Initialize with action to execute."""
        self.__action__ = action

    def failure(self, failure_handler: FailureHandler) -> ActionFailure[T]:
        """Configure error handler and advance to next state."""
        return ActionFailure(self.__action__, failure_handler)


@final
class ActionFailure[T]:
    """Action builder with failure handler configured, awaiting success handler."""

    def __init__(self, action: Action[T], failure_handler: FailureHandler) -> None:
        """Initialize with action and failure handler."""
        self._action = action
        self._failure_handler = failure_handler

    def success(self, success_handler: SuccHandler) -> ActionSuccess[T]:
        """Configure success handler and advance to executable state."""
        return ActionSuccess(self._action, self._failure_handler, success_handler)


@final
class ActionSuccess[T]:
    """Fully configured action builder, ready for execution."""

    def __init__(
        self,
        action: Action[T],
        failure_handler: FailureHandler,
        success_handler: SuccHandler,
    ) -> None:
        """Initialize with action and both handlers."""
        self.__action__ = action
        self.__failure_handler__ = failure_handler
        self.__success_handler__ = success_handler

    def execute(self) -> ActionChain[T]:
        """Execute action and call appropriate handler based on result.

        Flow:
            1. Call action() to get Result[T]
            2. If Fail: call failure_handler(error)
            3. If Ok: call success_handler()
            4. Return ActionChain with result

        Example:
            >>> chain = (
            ...     ActionStart(lambda: Ok(42))
            ...     .failure(lambda e: print(f"Error: {e}"))
            ...     .success(lambda: print("Success"))
            ...     .execute()
            ... )

        """
        result = self.__action__()

        if is_fail(result):
            self.__failure_handler__(result.error)
            return ActionChain(has_failed=True, result=result)

        self.__success_handler__()
        return ActionChain(has_failed=False, result=result)


@final
class NeutralActionStart[T]:
    """Neutral action builder that short-circuits (on failure rail).

    When a previous action failed, subsequent actions become "neutral" -
    they accept the same builder API but don't execute. This implements
    railway short-circuiting while maintaining fluent API.
    """

    def __init__(self, *, result: Result[T] | None) -> None:
        """Initialize with failure result from previous action."""
        self._result = result

    def failure(self, *args, **kwargs) -> NeutralActionFailure[T]:  # noqa: ARG002
        """Accept failure handler (ignored) and continue short-circuit."""
        return NeutralActionFailure(result=self._result)


@final
class NeutralActionFailure[T]:
    """Neutral action builder in failure-configured state (no-op)."""

    def __init__(self, *, result: Result[T] | None) -> None:
        """Initialize with failure result."""
        self._result = result

    def success(self, *args, **kwargs) -> NeutralActionSuccess[T]:  # noqa: ARG002
        """Accept success handler (ignored) and continue short-circuit."""
        return NeutralActionSuccess(result=self._result)


@final
class NeutralActionSuccess[T]:
    """Neutral action builder in success-configured state (no-op)."""

    def __init__(self, *, result: Result[T] | None) -> None:
        """Initialize with failure result."""
        self._result = result

    def execute(self) -> ActionChain[T]:
        """Return failed chain without executing (short-circuit)."""
        return ActionChain(has_failed=True, result=self._result)


@final
class ActionChain[T]:
    """Executed action chain with result and railway track position.

    Represents state after action execution:
    - Which rail? (success or failure)
    - What result? (Ok or Fail)

    Provides .then() to chain additional actions with railway switching.

    Example:
        >>> chain1 = action1.failure(h1).success(h2).execute()
        >>> if chain1.is_ok():
        ...     chain2 = chain1.then(action2).failure(h3).success(h4).execute()

    """

    def __init__(self, *, has_failed: bool, result: Result[T] | None) -> None:
        """Initialize with execution result and failure status."""
        self._has_failed = has_failed
        self._result = result

    def result(self) -> Result[T] | None:
        """Get execution result (Ok, Fail, or None if skipped)."""
        return self._result

    def then(
        self, action_or_start: Action[T] | ActionStart[T]
    ) -> ActionStart[T] | NeutralActionStart[T]:
        """Chain another action with railway switching logic.

        Railway switching:
        - If succeeded: return ActionStart (action executes)
        - If failed: return NeutralActionStart (short-circuit)

        Example:
            >>> chain2 = chain1.then(action2).failure(h).success(h).execute()
            >>> # action2 only executes if chain1 succeeded

        """
        if self._has_failed:
            return NeutralActionStart(result=self._result)

        if isinstance(action_or_start, ActionStart):
            action = action_or_start.__action__
        else:
            action = action_or_start

        return ActionStart(action)

    def has_failed(self) -> bool:
        """Check if chain is on failure rail."""
        return self._has_failed

    def is_ok(self) -> bool:
        """Check if chain is on success rail."""
        return not self._has_failed
