"""Generic driver builder with profile/temp dir lifecycle management."""

import shutil
import tempfile
from contextlib import suppress
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Callable

    from ocarina.custom_types.built_web_driver import BuiltWebDriver


class DriverBuilder[Driver]:
    """Manages temp profile dir lifecycle and builds (driver, dispose) pair.

    build_driver receives the profile directory path and returns a ready driver.
    All setup (implicit wait, options, etc.) belongs in build_driver.
    """

    def __init__(  # noqa: D107
        self,
        *,
        build_driver: Callable[[str], Driver],
        profile_path: str | None = None,
        tmp_dir_prefix: str = ".driver_profile_",
    ) -> None:
        self._build_driver = build_driver
        self._profile_path = profile_path
        self._tmp_dir_prefix = tmp_dir_prefix
        self._tmp_dir: tempfile.TemporaryDirectory[str] | None = None

    def build(self) -> BuiltWebDriver[Driver]:
        """Return (driver, dispose). dispose() quits driver and cleans temp dir."""
        tmp_dir, profile_path = self._prepare_profile()

        driver = self._build_driver(profile_path)

        def dispose() -> None:
            with suppress(Exception):
                driver.quit()  # type: ignore[attr-defined]
            with suppress(Exception):
                tmp_dir.cleanup()

        return driver, dispose

    def _prepare_profile(self) -> tuple[tempfile.TemporaryDirectory[str], str]:
        """Create temp dir, optionally copying an existing profile into it."""
        try:
            tmp_dir = tempfile.TemporaryDirectory(
                prefix=self._tmp_dir_prefix, dir=str(Path.cwd())
            )
            if self._profile_path is not None:
                shutil.copytree(self._profile_path, tmp_dir.name, dirs_exist_ok=True)
        except Exception as exc:
            with suppress(Exception):
                tmp_dir.cleanup()
            msg = "Failed to prepare driver profile directory."
            raise RuntimeError(msg) from exc
        else:
            return tmp_dir, tmp_dir.name
