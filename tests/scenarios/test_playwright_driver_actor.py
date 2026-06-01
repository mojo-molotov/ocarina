"""Fast actor tests for PlaywrightDriver — no real browser required.

These exercise the owner-thread marshalling logic in isolation by patching
``sync_playwright`` with a mock, so no Chromium is launched. They run on any
machine where the ``playwright`` package is importable (CI included), without a
browser binary.
"""

# ruff: noqa: S101

import threading
import time
from pathlib import Path
from types import SimpleNamespace
from unittest import mock
from unittest.mock import MagicMock

import pytest

from ocarina.custom_errors.test_framework.driver_died import DriverDiedError
from ocarina.infra.playwright.driver import (
    PlaywrightDriver,
    _generate_unique_trace_path,
)
from ocarina.infra.playwright.driver_healthcheck import (
    playwright_driver_healthcheck,
)

# Wall-clock ceiling for "must not hang" assertions: generously above the tiny
# call budgets used in these tests, but far below any real-world hang.
_NO_HANG_TIMEOUT_S = 5.0


def _build_doubled(
    *, wait_timeout: int = 1, call_timeout_margin: float = 30.0
) -> PlaywrightDriver:
    """Build a PlaywrightDriver whose page is a mock (no real browser)."""
    fake_page = MagicMock()
    fake_page.title.return_value = "doubled"
    fake_context = MagicMock()
    fake_context.pages = [fake_page]
    fake_pw = MagicMock()
    fake_pw.chromium.launch_persistent_context.return_value = fake_context
    fake_sync = MagicMock(return_value=MagicMock(start=MagicMock(return_value=fake_pw)))

    with mock.patch("ocarina.infra.playwright.driver.sync_playwright", fake_sync):
        return PlaywrightDriver(
            browser="chromium",
            headless=True,
            wait_timeout=wait_timeout,
            user_data_dir="unused",
            call_timeout_margin=call_timeout_margin,
        )


def test_submit_returns_value_from_non_owner_thread() -> None:
    """submit() from a thread that is not the owner returns the marshalled value."""
    driver = _build_doubled()
    try:
        assert driver.submit(lambda page: page.title()) == "doubled"
    finally:
        driver.quit()


def test_reentrant_submit_raises_without_browser() -> None:
    """The owner-thread re-entrancy guard fires without needing a real browser."""
    driver = _build_doubled()
    try:
        with pytest.raises(RuntimeError, match="Re-entrant submit"):
            driver.submit(lambda _page: driver.submit(lambda _inner: None))
    finally:
        driver.quit()


def test_healthcheck_returns_silently_for_voluntarily_closed_driver() -> None:
    """A disposed driver is not a dead driver: the healthcheck must not raise.

    This is what keeps the screenshotter from logging a stacktrace when a
    benign teardown race lets a take_screenshot reach a closed driver.
    """
    driver = _build_doubled()
    driver.quit()
    assert driver.is_closed

    # Must not raise — voluntary disposal is not a crash.
    playwright_driver_healthcheck(driver)


def test_healthcheck_still_raises_when_alive_driver_actually_crashes() -> None:
    """Counter-regression: a real driver crash mid-test still raises DriverDiedError.

    The voluntary-close short-circuit must not hide a genuine failure.
    """
    fake_page = MagicMock()
    fake_page.title.side_effect = RuntimeError("simulated browser crash")
    fake_context = MagicMock()
    fake_context.pages = [fake_page]
    fake_pw = MagicMock()
    fake_pw.chromium.launch_persistent_context.return_value = fake_context
    fake_sync = MagicMock(return_value=MagicMock(start=MagicMock(return_value=fake_pw)))

    with mock.patch("ocarina.infra.playwright.driver.sync_playwright", fake_sync):
        driver = PlaywrightDriver(
            browser="chromium", headless=True, wait_timeout=1, user_data_dir="unused"
        )

    try:
        assert not driver.is_closed  # alive — submit raises because page.title() does
        with pytest.raises(DriverDiedError):
            playwright_driver_healthcheck(driver)
    finally:
        driver.quit()


def test_trace_name_retries_past_existing_file(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The trace-name generator skips an existing file and keeps names short."""
    ids = iter(["aaaaaaaa", "aaaaaaaa", "bbbbbbbb"])
    monkeypatch.setattr(
        "ocarina.infra.playwright.driver.uuid.uuid4",
        lambda: SimpleNamespace(hex=next(ids)),
    )
    # Pre-create the first id so the generator must retry past it.
    (tmp_path / "trace_aaaaaaaa.zip").touch()

    result = _generate_unique_trace_path(str(tmp_path))

    assert result == str(tmp_path / "trace_bbbbbbbb.zip")
    assert len(Path(result).stem) <= len("trace_") + 8  # short, not a 32-char uuid


def test_boot_times_out_into_driver_died_without_hanging() -> None:
    """A driver crash *during startup* raises DriverDiedError, fast.

    The original prod crash signature fired at the startup/smoke phase, and on
    the on-demand acquire() path nothing else would catch a boot hang — it would
    wedge the worker with the pool permit held. Booting must be bounded too.
    """
    release = threading.Event()
    fake_pw = MagicMock()
    fake_pw.chromium.launch_persistent_context.side_effect = (
        lambda *_args, **_kwargs: release.wait()
    )
    fake_sync = MagicMock(return_value=MagicMock(start=MagicMock(return_value=fake_pw)))

    started = time.monotonic()
    try:
        with (
            mock.patch("ocarina.infra.playwright.driver.sync_playwright", fake_sync),
            pytest.raises(DriverDiedError),
        ):
            PlaywrightDriver(
                browser="chromium",
                headless=True,
                wait_timeout=0,
                user_data_dir="unused",
                call_timeout_margin=0.2,
            )
        assert time.monotonic() - started < _NO_HANG_TIMEOUT_S
    finally:
        release.set()  # let the abandoned owner-thread boot finish


def test_submit_times_out_into_driver_died_without_hanging() -> None:
    """A call that never returns (dead transport) raises DriverDiedError, fast.

    Simulates the prod symptom: the node driver crashed, so the owner thread is
    wedged on the dead pipe and the marshalled call never completes. submit()
    must bound the wait and surface DriverDiedError instead of hanging forever.
    """
    driver = _build_doubled(wait_timeout=0, call_timeout_margin=0.2)
    release = threading.Event()
    try:
        started = time.monotonic()
        with pytest.raises(DriverDiedError) as excinfo:
            driver.submit(lambda _page: release.wait())
        elapsed = time.monotonic() - started

        # Bounded by the budget (0.2s) — proves we did not hang on the dead call.
        assert elapsed < _NO_HANG_TIMEOUT_S
        # The original timeout is chained for diagnosis.
        assert excinfo.value.__cause__ is not None
        assert driver.is_dead
        assert driver.is_closed
    finally:
        release.set()  # let the abandoned owner-thread task finish
        driver.quit()


def test_dead_driver_rejects_further_use() -> None:
    """Once dead, submit() and the healthcheck both raise DriverDiedError."""
    driver = _build_doubled(wait_timeout=0, call_timeout_margin=0.2)
    release = threading.Event()
    try:
        with pytest.raises(DriverDiedError):
            driver.submit(lambda _page: release.wait())

        # Subsequent calls short-circuit to DriverDiedError (not RuntimeError,
        # not a hang) so the driver is never silently mistaken for alive.
        with pytest.raises(DriverDiedError):
            driver.submit(lambda page: page.title())
        with pytest.raises(DriverDiedError):
            playwright_driver_healthcheck(driver)
    finally:
        release.set()
        driver.quit()


def test_dispose_does_not_hang_after_driver_dies() -> None:
    """Disposing a dead driver must return promptly while its owner is wedged.

    This is the disposal-side of the hang, exactly as it happens in production:
    WebDriversPool.acquire() disposes in its finally right after a call timed out
    into DriverDiedError. The owner thread is still stuck on the dead pipe, so a
    quit() that joined it would sequester the semaphore permit for the life of
    the process. It must walk away instead.
    """
    driver = _build_doubled(wait_timeout=0, call_timeout_margin=0.2)
    release = threading.Event()
    try:
        with pytest.raises(DriverDiedError):
            driver.submit(lambda _page: release.wait())

        # Owner thread is still wedged (release not set): dispose anyway.
        finished = threading.Event()

        def _dispose() -> None:
            driver.quit()
            finished.set()

        threading.Thread(target=_dispose, daemon=True).start()
        hung_msg = "quit() hung after the driver died"
        assert finished.wait(timeout=_NO_HANG_TIMEOUT_S), hung_msg
    finally:
        release.set()  # let the abandoned owner-thread task finish
