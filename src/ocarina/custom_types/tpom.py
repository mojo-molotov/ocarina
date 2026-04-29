"""TPOM generic type for Page Object Model classes.

Type variable constrained to POMBase subclasses, enabling type-safe
operations on page objects with proper IDE support and type checking.

Example:
    >>> def act(page: TPOM, action: Callable[[TPOM], Result[TPOM]]):
    ...     return ActionStart(lambda: action(page))
    ...
    >>> login_page = LoginPage(driver)
    >>> chain = act(login_page, lambda p: p.enter_username("user"))
    >>> # Type preserved: ActionStart[LoginPage]

"""

from typing import TYPE_CHECKING, TypeVar

if TYPE_CHECKING:
    from ocarina.pom.base import POMBase

TPOM = TypeVar("TPOM", bound="POMBase")
"""Type variable for POM classes, bounded to POMBase.

Ensures type consistency across page object operations while preserving
concrete page types (LoginPage, WelcomePage, etc.) for IDE autocomplete
and static type checking.
"""
