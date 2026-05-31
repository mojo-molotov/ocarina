"""Page Object Model base class.

This module defines POMBase, the universal abstract base class for all
page objects, independent of browser automation framework.

The POM pattern encapsulates:
- Page verification (verify() method)
- Page actions (methods to interact with elements)
- Page elements (locators, element references)

POMBase provides a minimal, framework-agnostic interface that works with
Selenium, Playwright, Puppeteer, or any other browser automation tool.

Example:
    >>> class LoginPage(POMBase):
    ...     def __init__(self, driver: WebDriver):
    ...         self._driver = driver
    ...
    ...     def verify(self, timeout: float | None = None) -> Self:
    ...         WebDriverWait(self._driver, timeout or 10).until(
    ...             EC.presence_of_element_located((By.ID, "login-form"))
    ...         )
    ...         return self
    ...
    ...     def enter_username(self, username: str) -> Self:
    ...         self._driver.find_element(By.ID, "username").send_keys(username)
    ...         return self

"""

from abc import ABC, abstractmethod
from typing import Self


class POMBase(ABC):
    """Abstract base class for Page Object Model.

    Defines the universal contract all page objects must follow, regardless
    of the underlying browser automation framework (Selenium, Playwright, etc.).

    The only required method is verify(), which checks that the browser is
    on the expected page. All other page-specific functionality (actions,
    element access, etc.) is left to concrete implementations.

    Subclassing guidelines:
        - Implement verify() with page-specific checks
        - Return Self from methods for fluent API
        - Raise appropriate exceptions on verification failure
        - Store driver/page instance as needed by framework

    Example (Selenium):
        >>> class LoginPage(POMBase):
        ...     def __init__(self, driver: WebDriver):
        ...         self._driver = driver
        ...
        ...     def verify(self, timeout: float | None = None) -> Self:
        ...         WebDriverWait(self._driver, timeout or 10).until(
        ...             EC.presence_of_element_located((By.ID, "login-form"))
        ...         )
        ...         return self

    """

    @abstractmethod
    def verify(self, *, timeout: float | None = None) -> Self:
        """Verify that the browser is on the expected page.

        Checks for page-specific indicators such as unique elements, URL
        patterns, or page content. This method is typically called after
        navigation or page transitions to confirm the correct page loaded.

        Args:
            timeout: Maximum seconds to wait for verification. If None,
                    implementations should use a sensible default (typically 10s).

        Returns:
            Self for method chaining.

        Raises:
            Implementation-specific exceptions when verification fails
            (e.g., TimeoutException, PageVerificationError).

        Example:
            >>> def verify(self, timeout: float | None = None) -> Self:
            ...     WebDriverWait(self._driver, timeout or 10).until(
            ...         EC.presence_of_element_located((By.ID, "unique-element"))
            ...     )
            ...     return self

        """
        ...

    @abstractmethod
    def get_current_title(self) -> str:
        """Get the current page title (empty string if no <title>)."""
        ...
