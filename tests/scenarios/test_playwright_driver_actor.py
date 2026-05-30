"""Fast actor tests for PlaywrightDriver — no real browser required.

These exercise the owner-thread marshalling logic in isolation by patching
``sync_playwright`` with a mock, so no Chromium is launched. They run on any
machine where the ``playwright`` package is importable (CI included), without a
browser binary.
"""

# ruff: noqa: S101

from pathlib import Path
from types import SimpleNamespace
from unittest import mock
from unittest.mock import MagicMock

import pytest

from ocarina.infra.playwright.driver import (
    PlaywrightDriver,
    _generate_unique_trace_path,
)


def _build_doubled() -> PlaywrightDriver:
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
            browser="chromium", headless=True, wait_timeout=1, user_data_dir="unused"
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
