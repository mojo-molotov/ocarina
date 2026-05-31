"""Watcher: background daemon that polls a callback during test execution.

Deterministic tests use threading.Event for synchronization rather than sleeping
on wall-clock time.
"""

# ruff: noqa: S101

import threading
from dataclasses import dataclass, field
from typing import Any

import allure
import pytest

from ocarina.dsl.testing.watcher import Watcher
from ocarina.opinionated.loggers.muted_logger import MutedLogger

from .conftest import FakeDriver

EPIC = "Watcher"
FEATURE = "Watcher"
LAYER = "unit"


@dataclass
class RecordingHooks:
    """Captures every call made to the logger and screenshot callable."""

    messages: list[str] = field(default_factory=list)
    screenshots: list[tuple[Any, str]] = field(default_factory=list)

    def logger(self) -> Any:  # noqa: ANN401, D102
        hooks = self

        class _L(MutedLogger):  # type: ignore[misc]
            def info(self, msg: str, *args, **kwargs) -> None:  # noqa: ARG002
                hooks.messages.append(msg)

        return _L()

    def take_screenshot(self, driver, logger, category) -> None:  # noqa: ANN001, ARG002, D102
        self.screenshots.append((driver, category))


@allure.epic(EPIC)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.feature(FEATURE)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.tag("watcher", "lifecycle")  # type: ignore[no-untyped-call,untyped-decorator]
@allure.severity(allure.severity_level.CRITICAL)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.label("layer", LAYER)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.title(  # type: ignore[no-untyped-call,untyped-decorator]
    "start spawns a thread that calls the callback with the injected driver; stop joins it"  # noqa: E501
)
def test_watcher_starts_and_stops() -> None:  # noqa: D103
    seen_driver: list[FakeDriver] = []
    invoked = threading.Event()

    def callback(w: Watcher[FakeDriver]) -> None:
        seen_driver.append(w.driver)
        invoked.set()

    watcher = Watcher[FakeDriver](callback=callback, name="banner", poll_interval=0.15)
    hooks = RecordingHooks()
    driver = FakeDriver()

    watcher.start(driver, hooks.logger(), hooks.take_screenshot)
    try:
        assert invoked.wait(timeout=2.0), "callback never fired"
    finally:
        watcher.stop()

    assert seen_driver
    assert seen_driver[0] is driver


@allure.epic(EPIC)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.feature(FEATURE)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.tag("watcher", "lifecycle")  # type: ignore[no-untyped-call,untyped-decorator]
@allure.severity(allure.severity_level.MINOR)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.label("layer", LAYER)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.title("stop() called before start() is a safe no-op")  # type: ignore[no-untyped-call,untyped-decorator]
def test_stop_before_start_is_noop() -> None:  # noqa: D103
    watcher = Watcher[FakeDriver](
        callback=lambda _: None, name="idle", poll_interval=0.15
    )
    watcher.stop()  # must not raise, must not block


@allure.epic(EPIC)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.feature(FEATURE)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.tag("watcher", "error-isolation")  # type: ignore[no-untyped-call,untyped-decorator]
@allure.severity(allure.severity_level.CRITICAL)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.label("layer", LAYER)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.title("Exceptions in the callback are swallowed; subsequent polls still happen")  # type: ignore[no-untyped-call,untyped-decorator]
def test_callback_exception_does_not_kill_the_thread() -> None:  # noqa: D103
    calls = {"count": 0}
    second_poll = threading.Event()

    def callback(_w: Watcher[FakeDriver]) -> None:
        calls["count"] += 1
        if calls["count"] == 1:
            msg = "boom"
            raise RuntimeError(msg)
        second_poll.set()

    watcher = Watcher[FakeDriver](callback=callback, name="flaky", poll_interval=0.15)
    hooks = RecordingHooks()

    watcher.start(FakeDriver(), hooks.logger(), hooks.take_screenshot)
    try:
        assert second_poll.wait(timeout=2.0), "thread died after exception"
    finally:
        watcher.stop()


@allure.epic(EPIC)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.feature(FEATURE)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.tag("watcher", "report")  # type: ignore[no-untyped-call,untyped-decorator]
@allure.severity(allure.severity_level.NORMAL)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.label("layer", LAYER)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.title(  # type: ignore[no-untyped-call,untyped-decorator]
    "report() emits a log line and captures a screenshot via the injected hooks"
)
def test_report_logs_and_screenshots() -> None:  # noqa: D103
    reported = threading.Event()

    def callback(w: Watcher[FakeDriver]) -> None:
        if not reported.is_set():
            w.report("something happened", label="CUSTOM")
            reported.set()

    watcher = Watcher[FakeDriver](
        callback=callback, name="reporter", poll_interval=0.15
    )
    hooks = RecordingHooks()
    driver = FakeDriver()

    watcher.start(driver, hooks.logger(), hooks.take_screenshot)
    try:
        assert reported.wait(timeout=2.0)
    finally:
        watcher.stop()

    assert hooks.messages == ["something happened"]
    assert hooks.screenshots == [(driver, "CUSTOM")]


@allure.epic(EPIC)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.feature(FEATURE)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.tag("watcher", "report")  # type: ignore[no-untyped-call,untyped-decorator]
@allure.severity(allure.severity_level.MINOR)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.label("layer", LAYER)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.title("report() is a silent no-op when called before start()")  # type: ignore[no-untyped-call,untyped-decorator]
def test_report_before_start_is_silent() -> None:  # noqa: D103
    hooks = RecordingHooks()
    watcher = Watcher[FakeDriver](
        callback=lambda _: None, name="idle", poll_interval=0.15
    )

    watcher.report("too early")

    assert hooks.messages == []
    assert hooks.screenshots == []


@allure.epic(EPIC)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.feature(FEATURE)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.tag("watcher", "report", "teardown-race")  # type: ignore[no-untyped-call,untyped-decorator]
@allure.severity(allure.severity_level.CRITICAL)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.label("layer", LAYER)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.title(  # type: ignore[no-untyped-call,untyped-decorator]
    "report() called by a callback still in flight after stop() is a silent no-op"
)
def test_report_after_stop_is_silent_even_when_callback_is_in_flight() -> None:  # noqa: D103
    # Reproduces the teardown race deterministically:
    # 1. Callback enters and signals it is running, then waits.
    # 2. Main thread sees the signal and calls stop() — stop_event gets set
    #    and join() returns (bounded), but the callback is still in flight.
    # 3. Main thread releases the callback. It calls report().
    # 4. report() must observe the set stop_event and skip both logging and
    #    the screenshot — otherwise the screenshot would race with disposal
    #    and produce a noisy DriverDiedError stacktrace under load.
    in_callback = threading.Event()
    proceed = threading.Event()

    def callback(w: Watcher[FakeDriver]) -> None:
        in_callback.set()
        proceed.wait(timeout=2.0)
        w.report("late", label="LATE")

    watcher = Watcher[FakeDriver](callback=callback, name="leaky", poll_interval=0.05)
    hooks = RecordingHooks()
    driver = FakeDriver()

    watcher.start(driver, hooks.logger(), hooks.take_screenshot)
    assert in_callback.wait(timeout=2.0), "callback never started"

    watcher.stop()  # sets _stop_event; join times out because callback is in flight
    proceed.set()  # release the callback so it calls report()

    # Give the leaked thread a moment to finish its (now no-op) report() call.
    thread = watcher._thread  # noqa: SLF001
    assert thread is not None
    thread.join(timeout=2.0)
    assert not thread.is_alive(), "leaked thread did not exit after release"

    assert hooks.messages == []
    assert hooks.screenshots == []


@allure.epic(EPIC)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.feature(FEATURE)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.tag("watcher", "lifecycle")  # type: ignore[no-untyped-call,untyped-decorator]
@allure.severity(allure.severity_level.MINOR)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.label("layer", LAYER)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.title(  # type: ignore[no-untyped-call,untyped-decorator]
    "Accessing driver before start() raises RuntimeError with a clear message"
)
def test_driver_property_raises_before_start() -> None:  # noqa: D103
    watcher = Watcher[FakeDriver](
        callback=lambda _: None, name="idle", poll_interval=0.15
    )

    with pytest.raises(RuntimeError, match="before start"):
        _ = watcher.driver


@allure.epic(EPIC)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.feature(FEATURE)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.tag("watcher", "cache")  # type: ignore[no-untyped-call,untyped-decorator]
@allure.severity(allure.severity_level.NORMAL)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.label("layer", LAYER)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.title("cache is a mutable set and state persists across poll cycles")  # type: ignore[no-untyped-call,untyped-decorator]
def test_cache_persists_across_polls() -> None:  # noqa: D103
    cycles = threading.Semaphore(0)

    def callback(w: Watcher[FakeDriver]) -> None:
        w.cache.add(f"poll-{len(w.cache)}")
        cycles.release()

    watcher = Watcher[FakeDriver](callback=callback, name="cacher", poll_interval=0.15)
    hooks = RecordingHooks()

    watcher.start(FakeDriver(), hooks.logger(), hooks.take_screenshot)
    try:
        # Wait for at least 3 polls to confirm cache is shared across cycles.
        for _ in range(3):
            assert cycles.acquire(timeout=2.0)
    finally:
        watcher.stop()

    assert len(watcher.cache) >= 3  # noqa: PLR2004
    assert "poll-0" in watcher.cache
    assert "poll-1" in watcher.cache
    assert "poll-2" in watcher.cache


@allure.epic(EPIC)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.feature(FEATURE)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.tag("watcher", "lifecycle")  # type: ignore[no-untyped-call,untyped-decorator]
@allure.severity(allure.severity_level.CRITICAL)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.label("layer", LAYER)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.title(  # type: ignore[no-untyped-call,untyped-decorator]
    "A second start() terminates a leaked thread from a stop() that timed out"
)
def test_restart_terminates_leaked_thread() -> None:
    """Restart terminates leaked thread from a stop() that timed out.

    Regression: a slow callback that outruns stop()'s join timeout used to
    leak its thread, which would then resume polling against the *new*
    driver after the next start(). The fix gives each thread its own
    stop_event and sets the previous one on every start().
    """
    in_callback = threading.Event()
    release_callback = threading.Event()

    def slow_callback(_w: Watcher[FakeDriver]) -> None:
        in_callback.set()
        # Block until the test releases us, simulating a hung Selenium call.
        release_callback.wait(timeout=5.0)

    watcher = Watcher[FakeDriver](
        callback=slow_callback, name="hanger", poll_interval=0.15
    )
    hooks = RecordingHooks()

    # Attempt 1: start, wait until the callback is blocked inside.
    watcher.start(FakeDriver(), hooks.logger(), hooks.take_screenshot)
    assert in_callback.wait(timeout=2.0), "callback never entered"
    first_thread = watcher._thread  # noqa: SLF001
    assert first_thread is not None

    # stop() will time out (callback is blocked) but must not raise.
    watcher.stop()
    assert first_thread.is_alive(), "thread should still be alive after stop() timeout"

    # Attempt 2: start again. The fix must set the previous stop_event so the
    # leaked thread exits as soon as we release it (rather than racing with
    # the new thread on shared state).
    watcher.start(FakeDriver(), hooks.logger(), hooks.take_screenshot)
    second_thread = watcher._thread  # noqa: SLF001
    assert second_thread is not first_thread

    # Release the blocked callback. The leaked thread should observe its
    # (already-set) stop_event and exit; it must NOT loop again.
    release_callback.set()
    first_thread.join(timeout=2.0)

    try:
        assert not first_thread.is_alive(), (
            "leaked thread kept polling after a second start()"
        )
    finally:
        watcher.stop()
