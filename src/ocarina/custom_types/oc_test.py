"""Custom types for the E2E testing framework.

Type hierarchy:
    TestName    → str identifier for a test (must be unique per campaign)
    TestScenario → Factory: (WebDriver, ILogger) → Sequence[ChainRunner]
    ChainRunner  → Lazy execution wrapper for action chains

Architecture (Railway Oriented Programming):
    1. Define TestScenario  → pure, no side effects
    2. Test.spawn() calls it → returns ChainRunners
    3. Run each ChainRunner  → executes steps, triggers side effects
    4. Collect results       → aggregate success/failure

Design principles:
    - Scenarios are pure: side effects happen during ChainRunner execution
    - Use closures to capture driver/logger dependencies
    - Group same-page actions in the same drive_page() call

Example:
    >>> def my_scenario(driver: WebDriver, logger: ILogger):
    ...     page = MyPage(driver)
    ...     log_err = create_log_error_with_url(logger, driver)
    ...     log_ok  = create_log_success(logger)
    ...     return [
    ...         drive_page(
    ...             act(page, open_page)
    ...                 .failure(log_err("Failed to open"))
    ...                 .success(log_ok("Page opened")),
    ...         )
    ...     ]

"""

from collections.abc import Callable

from ocarina.custom_types.scenario import Scenario
from ocarina.custom_types.test_components import TestChain
from ocarina.ports.ilogger import ILogger

type TestName = str
"""Human-readable test identifier. Must be unique within a campaign.

Example:
    >>> name: TestName = "Verify dashboard displays after login"

"""

type TestScenario[Driver] = Callable[[Driver, ILogger], Scenario[Driver]]
"""Factory that defines all components of a test without executing them.

Generic over Driver — use SeleniumTestScenario for Selenium-specific tests.
Receives a driver and ILogger at runtime, returns a Scenario
encapsulating the test chain, optional setup/teardown effects,
and optional watchers.

Keep the function pure — side effects belong in the ChainRunners,
setup, teardown, and watchers, not in the scenario factory itself.

Example:
    >>> def scenario(driver: Driver, logger: ILogger) -> Scenario:
    ...     page = MyPage(driver)
    ...     return Scenario(
    ...         setup=lambda: seed_db(logger=logger),
    ...         test_chain=[
    ...             drive_page(act(page, action).failure(...).success(...))
    ...         ],
    ...         teardown=lambda: cleanup_db(logger=logger),
    ...     )

"""

type TestScenarioFragment[Driver] = Callable[[Driver, ILogger], TestChain]
"""Factory that defines a test's steps without executing them.

Generic over Driver — use SeleniumTestScenarioFragment for Selenium-specific tests.
Receives a driver and ILogger at runtime, returns a sequence of ChainRunners
to be executed sequentially (TestChain). Keep the function pure — side effects belong
in the ChainRunners, not in the scenario itself.

Example:
    >>> def scenario(driver: Driver, logger: ILogger) -> Sequence[ChainRunner]:
    ...     page = MyPage(driver)
    ...     return [drive_page(act(page, action).failure(...).success(...))]

"""
