"""Chain actions over a page.

Example:
    >>> def test_scenario(
    ...     driver: WebDriver,
    ...     logger: ILogger
    ... ) -> TestChain:
    ...     return [
    ...         drive_page(
    ...             act(login_page, open_login_page)
    ...                 .failure(log_error("Failed to open login page"))
    ...                 .success(log_success("Login page opened")),
    ...             act(login_page, enter_credentials)
    ...                 .failure(log_error("Failed to enter credentials"))
    ...                 .success(log_success("Credentials entered"))
    ...         ),
    ...         drive_page(
    ...             act(welcome_page, verify_welcome_page)
    ...                 .failure(log_error("Welcome page not found"))
    ...                 .success(log_success("Welcome page verified"))
    ...         )
    ...     ]

"""

from typing import TYPE_CHECKING

from ocarina.dsl.testing_with_railway.chain_actions import ChainRunner, chain_actions

if TYPE_CHECKING:
    from ocarina.custom_types.tpom import TPOM
    from ocarina.dsl.testing_with_railway.internals.action_chain import ActionSuccess


def drive_page(
    first: ActionSuccess[TPOM], *rest: ActionSuccess[TPOM]
) -> ChainRunner[TPOM]:
    """Chain actions over a page.

    Example:
        >>> def test_scenario(
        ...     driver: WebDriver,
        ...     logger: ILogger
        ... ) -> Sequence[ChainRunner[Any]]:
        ...     return [
        ...         drive_page(
        ...             act(login_page, open_login_page)
        ...                 .failure(log_error("Failed to open login page"))
        ...                 .success(log_success("Login page opened")),
        ...             act(login_page, enter_credentials)
        ...                 .failure(log_error("Failed to enter credentials"))
        ...                 .success(log_success("Credentials entered"))
        ...         ),
        ...         drive_page(
        ...             act(welcome_page, verify_welcome_page)
        ...                 .failure(log_error("Welcome page not found"))
        ...                 .success(log_success("Welcome page verified"))
        ...         )
        ...     ]

    """
    return chain_actions(first, *rest)
