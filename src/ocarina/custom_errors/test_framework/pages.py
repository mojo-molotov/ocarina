"""Page Object Model verification errors.

Defines exceptions for POM verification failures, raised when the actual
web page doesn't match the expected page object.

In POM, each page object has a verify() method checking for unique elements,
URLs, or titles. Verification failure means the test is on the wrong page.

Common scenarios:
- Navigation redirected to error page
- Login failed, redirected to login instead of dashboard
- Page didn't load or timed out
- JavaScript routing went to wrong state
- Expected element not found (page structure changed)

Example:
    >>> try:
    ...     login_page.verify()
    ... except PageVerificationError:
    ...     logger.error(f"Not on login page. URL: {driver.current_url}")
    ...     take_screenshot(driver)

"""

from typing import final


@final
class PageVerificationError(Exception):
    """Raised when page verification detects a mismatch.

    Indicates the current web page doesn't match the expected POM. Raised by
    POM verify() methods when identifying characteristics (elements, URL,
    title) don't match expectations.

    This is critical in E2E tests because:
    - Test is operating on wrong page
    - Subsequent actions will likely fail
    - Test flow deviated from expected path

    When raised, test should log, screenshot, and fail or attempt recovery.

    Example:
        >>> # In POM class
        >>> class LoginPage:
        ...     def verify(self) -> None:
        ...         try:
        ...             self.driver.find_element(By.ID, "login-form")
        ...         except NoSuchElementException as exc:
        ...             raise PageVerificationError(
        ...                 "Login page not detected: missing login form"
        ...             ) from exc

        >>> # In test with error handling
        >>> try:
        ...     welcome_page.verify()
        ... except PageVerificationError as exc:
        ...     logger.error(f"Verification failed: {exc}")
        ...     take_screenshot(driver, "VERIFICATION_FAILURE")
        ...     raise

    Note:
        Typically caught by test step handlers for logging (URL, screenshot)
        before failing or retrying. Should not be silently ignored.

    """
