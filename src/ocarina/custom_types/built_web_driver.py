"""BuiltWebDriver type for resource-safe WebDriver management.

This module defines a pattern for pairing WebDriver instances with
their cleanup functions, ensuring proper resource disposal and preventing
browser process leaks.

The pattern guarantees:
- Each driver has an associated cleanup function
- Explicit resource disposal
- Cleanup happens even in error scenarios
- Consistent lifecycle management

Used primarily by WebDriversPool for managing reusable driver instances.

Example:
    >>> def create_chrome_driver() -> BuiltSeleniumWebDriver:
    ...     options = ChromeOptions()
    ...     driver = webdriver.Chrome(options=options)
    ...
    ...     def dispose():
    ...         with suppress(Exception):
    ...             driver.quit()
    ...
    ...     return driver, dispose
    ...
    >>> driver, dispose = create_chrome_driver()
    >>> try:
    ...     driver.get("https://example.com")
    ... finally:
    ...     dispose()  # Cleanup guaranteed

"""

from ocarina.custom_types.effect import Effect

type BuiltWebDriver[Driver] = tuple[Driver, Effect]

"""WebDriver paired with its cleanup function.

Couples a WebDriver instance with a disposal function to ensure proper
resource cleanup. The tuple structure makes cleanup explicit and unavoidable.

Structure:
    - [0] WebDriver: Initialized WebDriver instance
    - [1] Effect: Cleanup function (typically calls driver.quit())

The cleanup Effect must:
- Call driver.quit() to close browser and end session
- Suppress all exceptions (use suppress or try/except)
- Never raise exceptions (cleanup is "fire and forget")

Example:
    >>> # Create driver with cleanup
    >>> def create_driver() -> BuiltSeleniumWebDriver:
    ...     driver = webdriver.Chrome()
    ...     return (driver, lambda: suppress(Exception)(driver.quit)())
    ...
    >>> # Use in pool
    >>> driver, dispose = pool.acquire()
    >>> try:
    ...     driver.get("https://example.com")
    ... finally:
    ...     dispose()  # Always cleanup

Note:
    Cleanup functions should NEVER raise exceptions. Suppress or log errors
    to prevent masking the original test failure.

See Also:
    - create_selenium_drivers_pool: Creates pools of BuiltSeleniumWebDriver instances
    - Effect: Type alias for side-effecting functions (Callable[[], None])
"""
