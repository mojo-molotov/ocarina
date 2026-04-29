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

    Example:
        >>> # Selenium
        ... class LoginPage(POMBase):
        ...     def __init__(self, driver: WebDriver):
        ...         self._driver = driver
        ...
        ...     def verify(self, timeout: float | None = None) -> Self:
        ...         WebDriverWait(self._driver, timeout or 10).until(
        ...             EC.presence_of_element_located((By.ID, "login-form"))
        ...         )
        ...         return self

    Example:
        >>> # Playwright
        ... class LoginPage(POMBase):
        ...     def __init__(self, page: Page):
        ...         self._page = page
        ...
        ...     def verify(self, timeout: float | None = None) -> Self:
        ...         self._page.wait_for_selector("#login-form", timeout=timeout)
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
            >>> # Checking for unique element
            ... def verify(self, timeout: float | None = None) -> Self:
            ...     WebDriverWait(self._driver, timeout or 10).until(
            ...         EC.presence_of_element_located((By.ID, "unique-element"))
            ...     )
            ...     return self

        Example:
            >>> # Checking URL pattern
            ... def verify(self, timeout: float | None = None) -> Self:
            ...     if "/login" not in self._driver.current_url:
            ...         raise PageVerificationError("Not on login page")
            ...     return self

        """
        ...

    @abstractmethod
    def get_current_title(self) -> str:
        """Get the current page title from the browser.

        Returns the text content of the page's <title> element.
        Used for:
        - Page verification (check title contains expected text)
        - Logging (include title in error messages)
        - Debugging (identify which page we're on)

        Returns:
            str: The page title as a string.
                Empty string if no title element exists.

        Example (manual implementation):
            >>> def get_current_title(self) -> str:
            ...     return self._driver.title

        Example (using in verification):
            >>> def verify(self, timeout: float | None = None) -> Self:
            ...     if "Login" not in self.get_current_title():
            ...         raise PageVerificationError("Not on login page")
            ...     return self

        Example (using in logging):
            >>> def log_current_page(self) -> None:
            ...     logger.info(f"Current page: {self.get_current_title()}")

        Note:
            Most implementations should use SeleniumTitleMixin instead of
            implementing this manually. The mixin provides a standard
            implementation that simply returns self._driver.title.

        See Also:
            - SeleniumTitleMixin: Provides default implementation

        """
        ...
