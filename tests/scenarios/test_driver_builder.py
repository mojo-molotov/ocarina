"""DriverBuilder: manages a temp profile dir and pairs driver with dispose."""

# ruff: noqa: S101

from pathlib import Path

import allure

from ocarina.infra.driver_builder import DriverBuilder

EPIC = "DriverBuilder"
FEATURE = "Driver builder"
LAYER = "unit"


class FakeQuittableDriver:  # noqa: D101
    def __init__(self, profile_path: str) -> None:  # noqa: D107
        self.profile_path = profile_path
        self.quit_called = False

    def quit(self) -> None:  # noqa: D102
        self.quit_called = True


@allure.epic(EPIC)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.feature(FEATURE)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.tag("driver", "lifecycle")  # type: ignore[no-untyped-call,untyped-decorator]
@allure.severity(allure.severity_level.CRITICAL)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.label("layer", LAYER)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.title(  # type: ignore[no-untyped-call,untyped-decorator]
    "build() returns (driver, dispose); dispose quits driver and removes temp profile dir"  # noqa: E501
)
def test_build_and_dispose_full_lifecycle(tmp_path: Path, monkeypatch) -> None:  # noqa: ANN001, D103
    monkeypatch.chdir(tmp_path)

    builder = DriverBuilder[FakeQuittableDriver](
        build_driver=FakeQuittableDriver, tmp_dir_prefix=".prof_"
    )

    driver, dispose = builder.build()

    profile_dir = Path(driver.profile_path)
    assert profile_dir.exists()
    assert profile_dir.parent == tmp_path
    assert profile_dir.name.startswith(".prof_")

    dispose()

    assert driver.quit_called is True
    assert not profile_dir.exists()


@allure.epic(EPIC)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.feature(FEATURE)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.tag("driver", "profile")  # type: ignore[no-untyped-call,untyped-decorator]
@allure.severity(allure.severity_level.NORMAL)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.label("layer", LAYER)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.title(  # type: ignore[no-untyped-call,untyped-decorator]
    "When a profile_path is provided, its contents are copied into the temp dir"
)
def test_existing_profile_is_copied_in(tmp_path: Path, monkeypatch) -> None:  # noqa: ANN001, D103
    monkeypatch.chdir(tmp_path)
    source_profile = tmp_path / "source_profile"
    source_profile.mkdir()
    (source_profile / "prefs.json").write_text('{"pref":1}')
    (source_profile / "cache").mkdir()
    (source_profile / "cache" / "data").write_text("cached")

    builder = DriverBuilder[FakeQuittableDriver](
        build_driver=FakeQuittableDriver,
        profile_path=str(source_profile),
        tmp_dir_prefix=".prof_",
    )

    driver, dispose = builder.build()
    try:
        profile_dir = Path(driver.profile_path)
        assert (profile_dir / "prefs.json").read_text() == '{"pref":1}'
        assert (profile_dir / "cache" / "data").read_text() == "cached"
    finally:
        dispose()


@allure.epic(EPIC)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.feature(FEATURE)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.tag("driver", "error-isolation")  # type: ignore[no-untyped-call,untyped-decorator]
@allure.severity(allure.severity_level.NORMAL)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.label("layer", LAYER)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.title("dispose() suppresses exceptions from driver.quit so cleanup still runs")  # type: ignore[no-untyped-call,untyped-decorator]
def test_dispose_swallows_quit_exceptions(tmp_path: Path, monkeypatch) -> None:  # noqa: ANN001, D103
    monkeypatch.chdir(tmp_path)

    class BrokenDriver:
        def __init__(self, profile_path: str) -> None:
            self.profile_path = profile_path

        def quit(self) -> None:
            msg = "driver already dead"
            raise RuntimeError(msg)

    builder = DriverBuilder[BrokenDriver](
        build_driver=BrokenDriver, tmp_dir_prefix=".prof_"
    )

    driver, dispose = builder.build()
    profile_dir = Path(driver.profile_path)

    dispose()  # must not raise

    assert not profile_dir.exists()
