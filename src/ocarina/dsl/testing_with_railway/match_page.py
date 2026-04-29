"""Conditional branching operator for adaptive pages.

Provides match_page() and when() as a DSL extension for handling pages
that can be in multiple states (A/B tests, optional banners, random modals,
maintenance pages, etc.).

Semantics:
    - Evaluates each when() condition in order (first match wins)
    - Executes the matching branch's ChainRunners sequentially
    - If no condition matches: Fail (on failure rail, short-circuits downstream)
    - If a branch's ChainRunner fails: Fail (same short-circuit behavior)
    - Returns a ChainRunner[Any] — integrates naturally in a scenario's list

Railway behavior:
    match_page is a ChainRunner like drive_page.
    It composes in a scenario list and participates in the same
    short-circuit logic: if a previous ChainRunner has failed,
    match_page is never executed (caller is responsible for that,
    as with all ChainRunners in Ocarina).

Example:
    >>> def scenario(driver: WebDriver, logger: ILogger) -> TestChain:
    ...     page = SomePage(driver=driver)
    ...
    ...     return [
    ...         drive_page(
    ...             act(page, open_page)
    ...                 .failure(log_error("Failed to open..."))
    ...                 .success(log_success("Opened!")),
    ...         ),
    ...         match_page(
    ...             branches=[
    ...                 when(
    ...                     page.has_cookie_banner,
    ...                     name="has_cookie_banner",
    ...                     then=[
    ...                         drive_page(
    ...                             act(page, dismiss_banner)
    ...                                 .failure(log_error("Failed to dismiss..."))
    ...                                 .success(log_success("Banner dismissed!")),
    ...                         ),
    ...                     ],
    ...                 ),
    ...                 when(
    ...                     lambda: not page.has_cookie_banner(),
    ...                     name="has_not_cookie_banner",
    ...                     then=[
    ...                         drive_page(
    ...                             act(page, verify_page)
    ...                                 .failure(log_error("Failed to verify..."))
    ...                                 .success(log_success("Page verified!")),
    ...                         ),
    ...                     ],
    ...                 ),
    ...             ],
    ...         ),
    ...         drive_page(
    ...             act(page, do_next_thing)
    ...                 .failure(log_error("Failed..."))
    ...                 .success(log_success("Done!")),
    ...         ),
    ...     ]

"""

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, final

from ocarina.custom_errors.test_framework.no_matching_branch import (
    NoMatchingBranchError,
)
from ocarina.dsl.testing_with_railway.chain_actions import ChainRunner
from ocarina.dsl.testing_with_railway.internals.action_chain import ActionChain
from ocarina.opinionated.loggers.muted_logger import MutedLogger
from ocarina.railway.result import Fail, Ok

if TYPE_CHECKING:
    from collections.abc import Sequence

    from ocarina.custom_types.test_components import TestChain
    from ocarina.custom_types.thunk import Thunk
    from ocarina.ports.ilogger import ILogger


@final
@dataclass(frozen=True)
class When:
    """A conditional branch: a guard and the ChainRunners to execute if it matches.

    Attributes:
        condition: A thunk returning True if this branch should execute.
        name: Name of the branch (logging purposes).
        then: ChainRunners to execute sequentially if condition is True.

    """

    condition: Thunk[bool]
    then: TestChain
    name: str = ""


when = When


def _run_branch(runners: TestChain) -> ActionChain[Any]:
    """Execute a branch's ChainRunners sequentially, short-circuiting on failure.

    Args:
        runners: ChainRunners to execute in order.

    Returns:
        The final ActionChain — either the first failed one, or the last ok one.

    """
    last: ActionChain[Any] | None = None

    for runner in runners:
        chain = runner.run()
        last = chain
        if chain.has_failed():
            return chain

    if last is None:
        return ActionChain(has_failed=False, result=Ok(value=None))

    return last


def _match_page_builder(  # noqa: ANN202
    *,
    raised_exceptions: tuple[type[BaseException], ...] = (),
):
    """Build a match_page function with exception policy.

    Args:
        raised_exceptions:
            Tuple of exception classes that MUST be re-raised during
            condition evaluation. All other exceptions are treated as
            a failed condition (i.e. equivalent to False).

    Returns:
        A match_page function.

    """

    def _match_page(logger: ILogger, branches: Sequence[When]) -> ChainRunner[Any]:
        """Conditional branching operator for adaptive pages.

        Evaluates each when() condition in declaration order.
        The first branch whose condition returns True is executed.
        If no branch matches, the ChainRunner fails with NoMatchingBranchError.

        Exception handling policy:
            - Exceptions listed in `raise_exceptions` are re-raised immediately.
            - All other exceptions raised by branch.condition() are
              interpreted as a non-matching condition (False).

        Args:
            logger: logger.
            branches: When instances declared with when(). Evaluated in order.

        Returns:
            ChainRunner[Any] — composes naturally in a scenario's ChainRunner list.

        Raises (via Fail on the railway):
            NoMatchingBranchError:
                If no when() condition returned True.

            Any exception explicitly listed in `raise_exceptions`:
                Re-raised during condition evaluation.

        """

        def _thunk() -> ActionChain[Any]:
            for index, branch in enumerate(branches):
                label = branch.name or f"branch[{index}]"

                try:
                    matched = branch.condition()
                    msg = f"match_page: '{label}' -> {matched}"
                    logger.debug(msg)

                except raised_exceptions as exc:
                    logger.exception("match_page: raising exception...", exc=exc)  # type: ignore[arg-type]
                    raise

                except Exception as exc:
                    msg = f"match_page: '{label}' raised"
                    logger.exception(msg, exc=exc)
                    matched = False

                if matched:
                    msg = f"match_page: '{label}' matched."
                    logger.info(msg)
                    return _run_branch(branch.then)

            return ActionChain(
                has_failed=True,
                result=Fail(
                    error=NoMatchingBranchError(
                        f"No when() branch matched out of {len(branches)} candidate(s)."
                    )
                ),
            )

        return ChainRunner(thunk=_thunk)

    return _match_page


def create_match_page(
    *,
    raised_exceptions: tuple[type[Exception], ...] = (),
):
    """Create a full-featured match_page function with exception and logging policy.

    Args:
        raised_exceptions:
            Tuple of exception classes that MUST be re-raised during
            condition evaluation. All other exceptions are treated as
            a failed condition (i.e. equivalent to False).

    Returns:
        A match_page function, injecting logger.

    Raises (via Fail on the railway):
        NoMatchingBranchError:
           If no when() condition returned True.

        Any exception explicitly listed in `raise_exceptions`:
            Re-raised during condition evaluation.

    Example:
        >>> match_page = create_match_page(
        ...     raise_exceptions=(ValueError, RuntimeError)
        ... )
        >>>
        >>> runner = match_page(
        ...     branches=[
        ...         when(
        ...             page.is_in_state_a,
        ...             name="s_a",
        ...             then=[
        ...                 drive_page(...)
        ...             ]
        ...         ),
        ...         when(
        ...             page.is_in_state_b,
        ...             name="s_b",
        ...             then=[
        ...                 drive_page(...)
        ...             ]
        ...         ),
        ...     ],
        ... )

    """

    def _match_page(  # noqa: ANN202
        *,
        logger: ILogger | None = None,
        branches: Sequence[When],
    ):
        _logger = MutedLogger() if logger is None else logger
        return _match_page_builder(raised_exceptions=raised_exceptions)(
            logger=_logger,
            branches=branches,
        )

    return _match_page
