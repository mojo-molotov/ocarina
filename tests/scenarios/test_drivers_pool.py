"""WebDriversPool: concurrency control, disposal, and warmup safeguards.

Checks observable behavior only: drivers are handed out, disposed after use,
bounded by max_size, and warmup detects stalled factories.
"""

# ruff: noqa: S101

import threading
import time

import allure
import pytest

from ocarina.infra.drivers_pool import WarmupTimeoutError, WebDriversPool

from .conftest import FakeDriver, make_built_driver, make_pool

EPIC = "WebDriversPool"
FEATURE = "Driver pool"
LAYER = "unit"


@allure.epic(EPIC)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.feature(FEATURE)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.tag("pool", "lifecycle")  # type: ignore[no-untyped-call,untyped-decorator]
@allure.severity(allure.severity_level.CRITICAL)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.label("layer", LAYER)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.title("acquire yields a driver and disposes it on context exit")  # type: ignore[no-untyped-call,untyped-decorator]
def test_acquire_yields_and_disposes() -> None:  # noqa: D103
    built = [make_built_driver()]
    pool = WebDriversPool[FakeDriver](create_driver=lambda: built[0], max_size=1)

    with pool.acquire() as driver:
        assert isinstance(driver, FakeDriver)
        assert driver.disposed is False

    assert built[0][0].disposed is True


@allure.epic(EPIC)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.feature(FEATURE)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.tag("pool", "capacity")  # type: ignore[no-untyped-call,untyped-decorator]
@allure.severity(allure.severity_level.NORMAL)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.label("layer", LAYER)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.title("Two sequential acquires both succeed and both drivers end up disposed")  # type: ignore[no-untyped-call,untyped-decorator]
def test_sequential_acquires_reuse_capacity() -> None:  # noqa: D103
    created: list[FakeDriver] = []

    def factory():  # noqa: ANN202
        driver, dispose = make_built_driver()
        created.append(driver)
        return driver, dispose

    pool = WebDriversPool[FakeDriver](create_driver=factory, max_size=1)

    with pool.acquire():
        pass
    with pool.acquire():
        pass

    assert len(created) == 2  # noqa: PLR2004
    assert all(d.disposed for d in created)


@allure.epic(EPIC)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.feature(FEATURE)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.tag("pool", "concurrency")  # type: ignore[no-untyped-call,untyped-decorator]
@allure.severity(allure.severity_level.BLOCKER)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.label("layer", LAYER)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.title("acquire blocks when max_size is reached; releasing unblocks the waiter")  # type: ignore[no-untyped-call,untyped-decorator]
def test_acquire_blocks_when_pool_is_saturated() -> None:  # noqa: D103
    pool = make_pool(max_size=1)

    first_in = threading.Event()
    release_first = threading.Event()
    second_acquired = threading.Event()

    def first_user() -> None:
        with pool.acquire():
            first_in.set()
            release_first.wait(timeout=2)

    def second_user() -> None:
        with pool.acquire():
            second_acquired.set()

    t1 = threading.Thread(target=first_user)
    t2 = threading.Thread(target=second_user)
    t1.start()

    first_in.wait(timeout=2)
    t2.start()

    # Second thread must not have entered its block yet
    assert not second_acquired.wait(timeout=0.3)

    release_first.set()
    t1.join(timeout=2)
    assert second_acquired.wait(timeout=2), "second thread never acquired after release"
    t2.join(timeout=2)


@allure.epic(EPIC)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.feature(FEATURE)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.tag("pool", "warmup")  # type: ignore[no-untyped-call,untyped-decorator]
@allure.severity(allure.severity_level.NORMAL)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.label("layer", LAYER)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.title("warmup pre-creates drivers up to max_size without stalling")  # type: ignore[no-untyped-call,untyped-decorator]
def test_warmup_fills_the_pool() -> None:  # noqa: D103
    created: list[FakeDriver] = []

    def factory():  # noqa: ANN202
        driver, dispose = make_built_driver()
        created.append(driver)
        return driver, dispose

    pool = WebDriversPool[FakeDriver](
        create_driver=factory, max_size=3, warmup_timeout=2.0
    )
    pool.warmup()

    # Three drivers created during warmup
    assert len(created) == 3  # noqa: PLR2004

    # Drivers are now served by subsequent acquires without calling the factory again
    before = len(created)
    with pool.acquire():
        pass
    assert len(created) == before


@allure.epic(EPIC)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.feature(FEATURE)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.tag("pool", "warmup", "error")  # type: ignore[no-untyped-call,untyped-decorator]
@allure.severity(allure.severity_level.NORMAL)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.label("layer", LAYER)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.title("warmup raises WarmupTimeoutError when the driver factory stalls")  # type: ignore[no-untyped-call,untyped-decorator]
def test_warmup_raises_on_stall() -> None:  # noqa: D103
    def stalling_factory():  # noqa: ANN202
        time.sleep(10)  # never returns within the warmup window
        return make_built_driver()

    pool = WebDriversPool[FakeDriver](
        create_driver=stalling_factory, max_size=2, warmup_timeout=0.2
    )

    with pytest.raises(WarmupTimeoutError):
        pool.warmup()
