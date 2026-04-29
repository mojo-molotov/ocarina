"""Low-level POM action operator for Railway Oriented Programming.

Provides create_act() as a building block for project-specific action wrappers.
NOT meant to be used directly - wrap it in your own act() function with
project-specific failure handling.

Recommended usage pattern:
    >>> # In your project, create a wrapper with custom logic
    >>> def act(pom: TPOM, action: Callable[[TPOM], TPOM]) -> ActionStart[TPOM]:
    ...     def failure_hook(pom: TPOM, exc: Exception) -> Fail:
    ...         # Detect HTTP error pages
    ...         title = pom.get_current_title()
    ...         if ERROR_PAGE_REGEX.match(title):
    ...             return Fail(error=HttpErrorPageReachedError(title))
    ...         return Fail(error=exc)
    ...
    ...     return create_act(
    ...         pom, action,
    ...         on_failure=failure_hook,
    ...         on_run_effect=increment_step_counter
    ...     )
    ...
    >>> # Then use your wrapper
    >>> act(page, lambda p: p.click_button())
    ...     .failure(log_error)
    ...     .success(log_success)
    ...     .execute()
"""

from typing import TYPE_CHECKING

from ocarina.dsl.testing_with_railway.internals.action_chain import ActionStart
from ocarina.opinionated.infra.act_counter import ActCounter as ThreadsBasedActCounter
from ocarina.railway.result import Fail, Ok, Result

if TYPE_CHECKING:
    from collections.abc import Callable

    from ocarina.custom_types.effect import Effect
    from ocarina.custom_types.tpom import TPOM


def create_act(
    pom: TPOM,
    action: Callable[[TPOM], TPOM],
    *,
    on_failure: Callable[[TPOM, Exception], Fail] | None = None,
    on_run_effect: Effect | None = None,
    act_counter_effect: Effect | None = None,
) -> ActionStart[TPOM]:
    """Low-level POM action wrapper for Railway pattern.

    Building block for project-specific action wrappers. Do NOT use directly -
    create your own act() function that wraps this with project logic.

    Wraps a Page Object Model action in Railway Result type:
    1. Execute optional side effect (e.g., step counting)
    2. Run action on POM
    3. On success: Return Ok[TPOM]
    4. On failure: Return Fail (or custom failure handler result)
    5. Wrap in ActionStart for Railway chain

    Args:
        pom: Page Object Model instance to operate on.
        action: Function performing action on POM, returns POM.
                Signature: (TPOM) -> TPOM
        on_failure: Optional custom failure handler.
                   Called when action raises exception.
                   Signature: (TPOM, Exception) -> Fail
                   If None, returns Fail(error=exc).
        on_run_effect: Optional side effect before action.
                      Signature: () -> None
        act_counter_effect: Optional side effect before action.
                      Signature: () -> None

    Returns:
        ActionStart[TPOM]: Railway builder for handler configuration.

    Example:
        >>> # Project-specific wrapper - RECOMMENDED
        ... def act(pom: TPOM, action: Callable[[TPOM], TPOM]) -> ActionStart[TPOM]:
        ...     def failure_hook(pom: TPOM, exc: Exception) -> Fail:
        ...         if "404" in pom.get_current_title():
        ...             return Fail(error=PageNotFoundError())
        ...         return Fail(error=exc)
        ...     return create_act(pom, action, on_failure=failure_hook)

    Note:
        All exceptions are caught and converted to Fail,
        but you can still use a custom on_failure hook to transform them.

    """

    def run_action() -> Result[TPOM]:
        """Execute action with error handling."""
        try:
            if act_counter_effect:
                act_counter_effect()
            else:
                ThreadsBasedActCounter().incr_act_call_count()

            if on_run_effect:
                on_run_effect()
            result_pom = action(pom)
            return Ok(result_pom)
        except Exception as exc:  # noqa: BLE001
            if on_failure:
                return on_failure(pom, exc)
            return Fail(error=exc)

    return ActionStart(run_action)
