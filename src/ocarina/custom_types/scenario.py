"""Test scenario — encapsulates all components of a test scenario.

A Scenario is the return type of test scenario function.
It centralizes all the concerns of a test: the test chain itself,
optional setup and teardown callbacks, and optional watchers.

Lifecycle (per attempt):
    1. setup()           — optional, free effect (DB, API, etc.)
       → raises: skip test_chain, jump to teardown, raise TestSetupError
       → ok: continue to test_chain

    2. test_chain        — the actual test (sequence of ChainRunners)

    3. teardown()        — optional, always executed, even on failure
       → raises: logged and ignored, does not affect TestResult

    If ALL attempts fail due to TestSetupError:
        → test is marked SKIPPED (not FAILED)
        → logger emits a message indicating setup keeps failing

Setup and teardown are driver-free and injectionless by design:
    They are plain Effects — () -> None.
    They are meant for infrastructure concerns: seeding a database,
    calling an API, cleaning up state. Selenium belongs in test_chain.
    Whatever context they need (logger, driver, config) must be
    captured in the closure at scenario construction time.

Watchers:
    Watchers run concurrently alongside test_chain.
    They are autonomous observers that operate independently
    of the test chain execution.
    They are started before test_chain and stopped after teardown.
    See ocarina.dsl.testing.watcher for implementation details.

Example:
    >>> def my_scenario(
    ...     driver: WebDriver,
    ...     logger: ILogger,
    ... ) -> Scenario:
    ...     page = MyPage(driver=driver)
    ...
    ...     return Scenario(
    ...         setup=lambda: seed_test_user(logger=logger),
    ...         test_chain=[
    ...             drive_page(
    ...                 act(page, open_page)
    ...                     .failure(log_error("Failed to open..."))
    ...                     .success(log_success("Opened!")),
    ...             ),
    ...         ],
    ...         teardown=lambda: delete_test_user(logger=logger),
    ...         watchers=[
    ...             MyWatcher(...),
    ...         ],
    ...     )

"""

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, final

if TYPE_CHECKING:
    from ocarina.custom_types.test_components import (
        TestChain,
        TestSetup,
        TestTeardown,
        TestWatchers,
    )


@final
@dataclass(frozen=True)
class Scenario[Driver]:
    """Encapsulates all components of a test scenario.

    Attributes:
        test_chain: The actual test — a sequence of ChainRunners
                    executed sequentially with Railway short-circuiting.
        setup:      Optional Effect executed before test_chain.
                    No DSL imposed. No driver. No injected logger.
                    Intended for infrastructure concerns: DB seeding,
                    API calls, state preparation.
                    Capture whatever context you need in the closure.
                    If it raises, test_chain is skipped, teardown runs,
                    and TestSetupError is raised.
        teardown:   Optional Effect executed after test_chain,
                    always — even on failure or setup error.
                    No DSL imposed. No driver. No injected logger.
                    Intended for infrastructure cleanup.
                    Capture whatever context you need in the closure.
                    Failures are logged and ignored.
        watchers:   Optional list of concurrent observers running
                    alongside test_chain.

    """

    test_chain: TestChain
    setup: TestSetup = field(default=None)
    teardown: TestTeardown = field(default=None)
    watchers: TestWatchers[Driver] | None = field(default=None)
