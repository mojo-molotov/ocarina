"""Loggers and post-run report plugins: observable outputs only."""

# ruff: noqa: S101

import json
from typing import TYPE_CHECKING

import allure

from ocarina.opinionated.loggers.file_logger import FileLogger
from ocarina.opinionated.loggers.muted_logger import MutedLogger
from ocarina.opinionated.loggers.print_logger import PrintLogger
from ocarina.opinionated.plugins.reports.pretty_print_results import (
    pretty_print_results,
)
from ocarina.opinionated.plugins.reports.results_to_json import generate_json_results
from ocarina.opinionated.plugins.reports.timing import timing
from ocarina.railway.result import Fail, Ok

if TYPE_CHECKING:
    from pathlib import Path

    from ocarina.custom_types.oc_test_layers import TestCycleResults


EPIC = "Loggers & reports"
FEATURE = "Loggers & reports"
LAYER = "unit"


def _sample_cycle_results() -> TestCycleResults:
    return {
        "Main": {
            "Login": {
                "login_ok": (Ok(value=None), 3, "login_ok"),
                "login_ko": (
                    Fail(error=RuntimeError("bad credentials")),
                    2,
                    "login_ko",
                ),
                "login_skipped": (None, -1, "login_skipped"),
            },
        },
    }


@allure.epic(EPIC)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.feature(FEATURE)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.tag("logger", "muted")  # type: ignore[no-untyped-call,untyped-decorator]
@allure.severity(allure.severity_level.MINOR)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.label("layer", LAYER)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.title("MutedLogger writes nothing to stdout or stderr")  # type: ignore[no-untyped-call,untyped-decorator]
def test_muted_logger_is_silent(capsys) -> None:  # noqa: ANN001, D103
    logger = MutedLogger()
    logger.info("should not appear")
    logger.error("neither should this")
    logger.success("nor this")

    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err == ""


@allure.epic(EPIC)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.feature(FEATURE)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.tag("logger", "print")  # type: ignore[no-untyped-call,untyped-decorator]
@allure.severity(allure.severity_level.NORMAL)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.label("layer", LAYER)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.title("PrintLogger emits message with taxonomy and prefix")  # type: ignore[no-untyped-call,untyped-decorator]
def test_print_logger_emits_prefix_and_taxonomy(capsys) -> None:  # noqa: ANN001, D103
    logger = (
        PrintLogger()
        .set_prefix(lambda: "[pfx]")
        .set_domain_taxonomy(("campaign", "suite"))
    )

    logger.info("hello")

    captured = capsys.readouterr()
    assert "[pfx]" in captured.out
    assert "campaign/suite" in captured.out
    assert "hello" in captured.out


@allure.epic(EPIC)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.feature(FEATURE)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.tag("logger", "file")  # type: ignore[no-untyped-call,untyped-decorator]
@allure.severity(allure.severity_level.NORMAL)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.label("layer", LAYER)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.title("FileLogger writes log lines to a file under the taxonomy path")  # type: ignore[no-untyped-call,untyped-decorator]
def test_file_logger_writes_to_disk(tmp_path: Path) -> None:  # noqa: D103
    logger = FileLogger(
        base_dir=tmp_path,
        with_flush_effect=False,
        with_fallback_on_print_logger_when_no_taxonomy_effect=False,
    )
    logger.set_domain_taxonomy(("campaign", "suite", "my_test"))
    logger.info("hello from file")

    # FileLogger writes on each call; cleanup() would flush-and-delete, so we
    # read the file while the logger is still alive.
    log_file = tmp_path / "campaign" / "suite" / "my_test.log"
    assert log_file.exists()
    assert "hello from file" in log_file.read_text()


@allure.epic(EPIC)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.feature(FEATURE)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.tag("logger", "file")  # type: ignore[no-untyped-call,untyped-decorator]
@allure.severity(allure.severity_level.NORMAL)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.label("layer", LAYER)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.title("FileLogger with a single-segment taxonomy writes at the base dir")  # type: ignore[no-untyped-call,untyped-decorator]
def test_file_logger_single_segment_taxonomy_writes_at_base(tmp_path: Path) -> None:  # noqa: D103
    logger = FileLogger(
        base_dir=tmp_path,
        with_flush_effect=False,
        with_fallback_on_print_logger_when_no_taxonomy_effect=False,
    )
    logger.set_domain_taxonomy(("campaign",))
    logger.info("solo segment")

    log_file = tmp_path / "campaign.log"
    assert log_file.exists()
    assert "solo segment" in log_file.read_text()


@allure.epic(EPIC)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.feature(FEATURE)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.tag("logger", "file", "fallback")  # type: ignore[no-untyped-call,untyped-decorator]
@allure.severity(allure.severity_level.NORMAL)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.label("layer", LAYER)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.title("FileLogger falls back to stdout when no taxonomy is set")  # type: ignore[no-untyped-call,untyped-decorator]
def test_file_logger_falls_back_to_print_when_no_taxonomy(  # noqa: D103
    tmp_path: Path,
    capsys,  # noqa: ANN001
) -> None:
    logger = FileLogger(
        base_dir=tmp_path,
        with_flush_effect=False,
        with_fallback_on_print_logger_when_no_taxonomy_effect=True,
    )
    # No taxonomy set -> nothing identifies a log file, fall back to printing.
    logger.info("no taxonomy here")

    captured = capsys.readouterr()
    assert "no taxonomy here" in captured.out
    assert list(tmp_path.iterdir()) == []  # no file was written


@allure.epic(EPIC)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.feature(FEATURE)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.tag("logger", "file", "cleanup")  # type: ignore[no-untyped-call,untyped-decorator]
@allure.severity(allure.severity_level.NORMAL)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.label("layer", LAYER)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.title("cleanup flushes the log file to stdout then deletes it")  # type: ignore[no-untyped-call,untyped-decorator]
def test_file_logger_cleanup_flushes_then_deletes(  # noqa: D103
    tmp_path: Path,
    capsys,  # noqa: ANN001
) -> None:
    logger = FileLogger(
        base_dir=tmp_path,
        with_flush_effect=True,
        with_fallback_on_print_logger_when_no_taxonomy_effect=False,
    )
    logger.set_domain_taxonomy(("campaign", "suite", "my_test"))
    logger.info("line to be flushed")
    log_file = tmp_path / "campaign" / "suite" / "my_test.log"
    assert log_file.exists()

    capsys.readouterr()  # drop the FileLogger output captured so far
    logger.cleanup()

    out = capsys.readouterr().out
    assert "Flush:" in out
    assert "line to be flushed" in out  # the file content was echoed
    assert not log_file.exists()  # and the file was recycled


@allure.epic(EPIC)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.feature(FEATURE)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.tag("logger", "file", "cleanup")  # type: ignore[no-untyped-call,untyped-decorator]
@allure.severity(allure.severity_level.MINOR)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.label("layer", LAYER)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.title("cleanup deletes the log file without flushing when the effect is off")  # type: ignore[no-untyped-call,untyped-decorator]
def test_file_logger_cleanup_deletes_without_flush(  # noqa: D103
    tmp_path: Path,
    capsys,  # noqa: ANN001
) -> None:
    logger = FileLogger(
        base_dir=tmp_path,
        with_flush_effect=False,
        with_fallback_on_print_logger_when_no_taxonomy_effect=False,
    )
    logger.set_domain_taxonomy(("campaign", "suite", "my_test"))
    logger.info("line that won't be echoed")
    log_file = tmp_path / "campaign" / "suite" / "my_test.log"
    assert log_file.exists()

    capsys.readouterr()
    logger.cleanup()

    out = capsys.readouterr().out
    assert "Flush:" not in out
    assert not log_file.exists()


@allure.epic(EPIC)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.feature(FEATURE)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.tag("logger", "file", "no-op")  # type: ignore[no-untyped-call,untyped-decorator]
@allure.severity(allure.severity_level.MINOR)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.label("layer", LAYER)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.title("FileLogger drops silently and cleanup is a safe no-op without a file")  # type: ignore[no-untyped-call,untyped-decorator]
def test_file_logger_no_taxonomy_drops_and_cleanup_is_safe(  # noqa: D103
    tmp_path: Path,
    capsys,  # noqa: ANN001
) -> None:
    logger = FileLogger(
        base_dir=tmp_path,
        with_flush_effect=True,
        with_fallback_on_print_logger_when_no_taxonomy_effect=False,
    )

    # No taxonomy and fallback disabled: the message is dropped entirely.
    logger.info("dropped")
    assert capsys.readouterr().out == ""
    assert list(tmp_path.iterdir()) == []

    # cleanup without a taxonomy must be a no-op, not an error.
    logger.cleanup()

    # cleanup with a taxonomy but before any line was written (no file yet)
    # must also be a safe no-op.
    logger.set_domain_taxonomy(("campaign", "suite", "my_test"))
    logger.cleanup()
    assert not (tmp_path / "campaign" / "suite" / "my_test.log").exists()


@allure.epic(EPIC)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.feature(FEATURE)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.tag("reports", "json")  # type: ignore[no-untyped-call,untyped-decorator]
@allure.severity(allure.severity_level.NORMAL)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.label("layer", LAYER)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.title("generate_json_results produces a JSON file with the expected structure")  # type: ignore[no-untyped-call,untyped-decorator]
def test_generate_json_results_writes_expected_shape(tmp_path: Path) -> None:  # noqa: D103
    generate_json_results(
        results=_sample_cycle_results(),
        output_dir=tmp_path,
        logger=MutedLogger(),
    )

    files = list(tmp_path.glob("*.json"))
    assert len(files) == 1

    payload = json.loads(files[0].read_text())
    assert set(payload.keys()) == {"Main"}
    assert set(payload["Main"]["Login"].keys()) == {
        "login_ok",
        "login_ko",
        "login_skipped",
    }

    ok_entry = payload["Main"]["Login"]["login_ok"][0]
    ko_entry = payload["Main"]["Login"]["login_ko"][0]
    assert ok_entry == {"status": "success"}
    assert ko_entry["status"] == "fail"
    assert "bad credentials" in ko_entry["error"]


@allure.epic(EPIC)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.feature(FEATURE)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.tag("reports", "pretty-print")  # type: ignore[no-untyped-call,untyped-decorator]
@allure.severity(allure.severity_level.NORMAL)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.label("layer", LAYER)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.title("pretty_print_results renders names, statuses and a summary line")  # type: ignore[no-untyped-call,untyped-decorator]
def test_pretty_print_renders_hierarchy_and_summary(capsys) -> None:  # noqa: ANN001, D103
    pretty_print_results(_sample_cycle_results(), with_colors=False)

    out = capsys.readouterr().out
    assert "Main" in out
    assert "Login" in out
    assert "login_ok" in out
    assert "login_ko" in out
    assert "PASSED" in out
    assert "FAILED" in out
    assert "SKIPPED" in out
    assert "Test results:" in out


@allure.epic(EPIC)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.feature(FEATURE)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.tag("reports", "timing")  # type: ignore[no-untyped-call,untyped-decorator]
@allure.severity(allure.severity_level.MINOR)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.label("layer", LAYER)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.title("timing context manager reports an elapsed duration on clean exit")  # type: ignore[no-untyped-call,untyped-decorator]
def test_timing_prints_elapsed(capsys) -> None:  # noqa: ANN001, D103
    with timing(prefix="Total:"):
        pass

    out = capsys.readouterr().out
    assert "Total:" in out
    assert "second" in out
