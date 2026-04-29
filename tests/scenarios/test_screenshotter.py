"""Screenshotter: thread-safe screenshot capture with optional full-page fallback.

Uses a minimal fake driver implementing the ScreenshotDriver protocol; no
Selenium dependency.
"""

# ruff: noqa: S101

from pathlib import Path

import allure

from ocarina.infra.screenshotter import Screenshotter, ScreenshotterConfig

from .conftest import FakeDriver

EPIC = "Screenshotter"
FEATURE = "Screenshotter"
LAYER = "unit"


class RecordingLogger:
    """Tiny ILogger-compatible recorder. Doesn't subclass ILogger to avoid
    needing to implement every abstract method; Screenshotter only touches
    .info / .error / .exception.
    """  # noqa: D205

    def __init__(self) -> None:  # noqa: D107
        self.info_msgs: list[str] = []
        self.error_msgs: list[str] = []
        self.exception_msgs: list[tuple[str, Exception | None]] = []

    def info(self, msg: str, *args, **kwargs) -> None:  # noqa: ARG002, D102
        self.info_msgs.append(msg)

    def error(self, msg: str, *args, **kwargs) -> None:  # noqa: ARG002, D102
        self.error_msgs.append(msg)

    def exception(  # noqa: D102
        self,
        msg: str,
        *args,  # noqa: ARG002
        exc: Exception | None = None,
        **kwargs,  # noqa: ARG002
    ) -> None:
        self.exception_msgs.append((msg, exc))


class SavingFakeDriver(FakeDriver):
    """Driver that actually writes a file to prove the path reached it."""

    def __init__(self, *, should_succeed: bool = True) -> None:  # noqa: D107
        super().__init__()
        self.calls: list[str] = []
        self.should_succeed = should_succeed

    def save_screenshot(self, path: str) -> bool:  # noqa: D102
        self.calls.append(path)
        if not self.should_succeed:
            return False
        Path(path).write_bytes(b"fake-png")
        return True


@allure.epic(EPIC)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.feature(FEATURE)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.tag("screenshot", "happy-path")  # type: ignore[no-untyped-call,untyped-decorator]
@allure.severity(allure.severity_level.NORMAL)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.label("layer", LAYER)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.title("Happy path: save_screenshot is called once and its path is logged")  # type: ignore[no-untyped-call,untyped-decorator]
def test_single_screenshot_is_written_and_logged(tmp_path: Path) -> None:  # noqa: D103
    driver = SavingFakeDriver()
    logger = RecordingLogger()
    screenshotter = Screenshotter(
        driver,
        logger,  # type: ignore[arg-type]
        ScreenshotterConfig(output_dir=tmp_path),
    )

    screenshotter.take_screenshot(prefix="login")

    assert len(driver.calls) == 1
    saved_path = Path(driver.calls[0])
    assert saved_path.parent == tmp_path
    assert saved_path.name.startswith("login_")
    assert saved_path.suffix == ".png"
    assert saved_path.exists()
    assert any("Screenshot: " in m for m in logger.info_msgs)


@allure.epic(EPIC)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.feature(FEATURE)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.tag("screenshot", "health-check")  # type: ignore[no-untyped-call,untyped-decorator]
@allure.severity(allure.severity_level.NORMAL)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.label("layer", LAYER)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.title("Health check failure short-circuits: no screenshot is taken")  # type: ignore[no-untyped-call,untyped-decorator]
def test_health_check_failure_prevents_capture(tmp_path: Path) -> None:  # noqa: D103
    driver = SavingFakeDriver()
    logger = RecordingLogger()

    def broken_health_check(_d: SavingFakeDriver) -> None:
        msg = "driver died"
        raise RuntimeError(msg)

    screenshotter = Screenshotter(
        driver,
        logger,  # type: ignore[arg-type]
        ScreenshotterConfig(output_dir=tmp_path, health_check=broken_health_check),
    )

    screenshotter.take_screenshot(prefix="x")

    assert driver.calls == []
    assert len(logger.exception_msgs) == 1
    assert "driver died" in str(logger.exception_msgs[0][1])


@allure.epic(EPIC)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.feature(FEATURE)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.tag("screenshot", "full-page", "fallback")  # type: ignore[no-untyped-call,untyped-decorator]
@allure.severity(allure.severity_level.NORMAL)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.label("layer", LAYER)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.title("save_full_page takes priority; save_screenshot is the fallback")  # type: ignore[no-untyped-call,untyped-decorator]
def test_full_page_tried_first_then_fallback(tmp_path: Path) -> None:  # noqa: D103
    driver = SavingFakeDriver()
    logger = RecordingLogger()
    full_page_calls: list[str] = []

    def full_page(_d: SavingFakeDriver, path: str) -> bool:
        full_page_calls.append(path)
        return False  # pretend full-page is unsupported

    screenshotter = Screenshotter(
        driver,
        logger,  # type: ignore[arg-type]
        ScreenshotterConfig(output_dir=tmp_path, save_full_page=full_page),
    )

    screenshotter.take_screenshot(prefix="fp")

    assert len(full_page_calls) == 1
    assert len(driver.calls) == 1
    assert full_page_calls[0] == driver.calls[0]


@allure.epic(EPIC)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.feature(FEATURE)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.tag("screenshot", "burst")  # type: ignore[no-untyped-call,untyped-decorator]
@allure.severity(allure.severity_level.NORMAL)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.label("layer", LAYER)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.title("Burst mode takes N shots with burst-style filenames")  # type: ignore[no-untyped-call,untyped-decorator]
def test_burst_mode_takes_multiple_shots(tmp_path: Path) -> None:  # noqa: D103
    driver = SavingFakeDriver()
    logger = RecordingLogger()
    screenshotter = Screenshotter(
        driver,
        logger,  # type: ignore[arg-type]
        ScreenshotterConfig(output_dir=tmp_path),
    )

    screenshotter.take_screenshot(prefix="anim", shots=3, burst_delay=0.0)

    assert len(driver.calls) == 3  # noqa: PLR2004
    # Filenames end with _1/_2/_3 for burst-mode
    suffixes = sorted(Path(p).stem.rsplit("_", 1)[-1] for p in driver.calls)
    assert suffixes == ["1", "2", "3"]
    assert len(logger.info_msgs) == 3  # noqa: PLR2004


@allure.epic(EPIC)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.feature(FEATURE)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.tag("screenshot", "error")  # type: ignore[no-untyped-call,untyped-decorator]
@allure.severity(allure.severity_level.NORMAL)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.label("layer", LAYER)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.title("save_screenshot returning False surfaces an error log")  # type: ignore[no-untyped-call,untyped-decorator]
def test_failed_save_is_logged_as_error(tmp_path: Path) -> None:  # noqa: D103
    driver = SavingFakeDriver(should_succeed=False)
    logger = RecordingLogger()
    screenshotter = Screenshotter(
        driver,
        logger,  # type: ignore[arg-type]
        ScreenshotterConfig(output_dir=tmp_path),
    )

    screenshotter.take_screenshot(prefix="nope")

    assert len(driver.calls) == 1
    assert len(logger.info_msgs) == 0
    assert any("FAILED TO TAKE SCREENSHOT" in m for m in logger.error_msgs)
