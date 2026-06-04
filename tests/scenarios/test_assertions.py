"""Example-based tests for the leaf assertion predicates.

These predicates encode concrete, branch-heavy rules (email shape, filename
rules, ISO date parsing, filesystem checks) where a hand-picked table reads
clearer than a property. Property-based laws for the pure/total predicates
live in ``test_invariants_properties.py``.

Each case asserts the contract: a valid input is a no-op, every invalid input
raises ``InvariantViolationError``.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import allure
import pytest

from ocarina.dsl.invariants.assertions import (
    is_dir,
    is_email,
    is_file,
    is_iso_date_string,
    is_iso_utc_date_string,
    is_valid_filename,
)
from ocarina.dsl.invariants.errors import InvariantViolationError

if TYPE_CHECKING:
    from pathlib import Path

EPIC = "Invariants DSL"
FEATURE = "Leaf assertion predicates"
LAYER = "unit"


# --- is_email -----------------------------------------------------------------


@allure.epic(EPIC)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.feature(FEATURE)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.tag("predicate", "is_email", "happy-path")  # type: ignore[no-untyped-call,untyped-decorator]
@allure.severity(allure.severity_level.NORMAL)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.label("layer", LAYER)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.title("is_email accepts a well-formed address")  # type: ignore[no-untyped-call,untyped-decorator]
@pytest.mark.parametrize("value", ["a@b.com", "user.name@sub.example.co.uk"])
def test_is_email_accepts_valid(value: str) -> None:  # noqa: D103
    is_email(value)  # should not raise


@allure.epic(EPIC)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.feature(FEATURE)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.tag("predicate", "is_email", "error")  # type: ignore[no-untyped-call,untyped-decorator]
@allure.severity(allure.severity_level.NORMAL)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.label("layer", LAYER)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.title("is_email rejects each malformed shape")  # type: ignore[no-untyped-call,untyped-decorator]
@pytest.mark.parametrize(
    "value",
    [
        "a b@c.com",  # whitespace
        "ab.com",  # missing '@'
        "a@@b.com",  # more than one '@'
        "@b.com",  # empty local part
        "a@",  # empty domain part
        "a@bcom",  # domain without a dot
    ],
)
def test_is_email_rejects_invalid(value: str) -> None:  # noqa: D103
    with pytest.raises(InvariantViolationError):
        is_email(value)


# --- is_valid_filename --------------------------------------------------------


@allure.epic(EPIC)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.feature(FEATURE)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.tag("predicate", "is_valid_filename", "happy-path")  # type: ignore[no-untyped-call,untyped-decorator]
@allure.severity(allure.severity_level.NORMAL)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.label("layer", LAYER)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.title("is_valid_filename accepts a cross-platform-safe name")  # type: ignore[no-untyped-call,untyped-decorator]
@pytest.mark.parametrize("value", ["my_test_runner", "report.docx", "a" * 255])
def test_is_valid_filename_accepts_valid(value: str) -> None:  # noqa: D103
    is_valid_filename(value)  # should not raise


@allure.epic(EPIC)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.feature(FEATURE)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.tag("predicate", "is_valid_filename", "error")  # type: ignore[no-untyped-call,untyped-decorator]
@allure.severity(allure.severity_level.NORMAL)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.label("layer", LAYER)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.title("is_valid_filename rejects each forbidden form")  # type: ignore[no-untyped-call,untyped-decorator]
@pytest.mark.parametrize(
    "value",
    [
        "",  # empty
        "a" * 256,  # too long
        "test/run",  # forbidden separator
        'na:me?"',  # forbidden characters
        "with\x00null",  # control character
        ".hidden",  # leading dot
        "trailing ",  # trailing space
        "CON",  # reserved device name
        "com1",  # reserved, case-insensitive
        "LPT9.txt",  # reserved stem with extension
    ],
)
def test_is_valid_filename_rejects_invalid(value: str) -> None:  # noqa: D103
    with pytest.raises(InvariantViolationError):
        is_valid_filename(value)


# --- is_iso_date_string -------------------------------------------------------


@allure.epic(EPIC)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.feature(FEATURE)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.tag("predicate", "is_iso_date_string", "happy-path")  # type: ignore[no-untyped-call,untyped-decorator]
@allure.severity(allure.severity_level.NORMAL)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.label("layer", LAYER)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.title("is_iso_date_string accepts valid ISO 8601 dates")  # type: ignore[no-untyped-call,untyped-decorator]
@pytest.mark.parametrize(
    "value",
    ["2025-12-18", "2025-12-18T10:30:00", "2025-12-18T10:30:00+02:00"],
)
def test_is_iso_date_string_accepts_valid(value: str) -> None:  # noqa: D103
    is_iso_date_string(value)  # should not raise


@allure.epic(EPIC)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.feature(FEATURE)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.tag("predicate", "is_iso_date_string", "error")  # type: ignore[no-untyped-call,untyped-decorator]
@allure.severity(allure.severity_level.NORMAL)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.label("layer", LAYER)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.title("is_iso_date_string rejects non-ISO strings")  # type: ignore[no-untyped-call,untyped-decorator]
@pytest.mark.parametrize("value", ["invalid", "2025-13-40", ""])
def test_is_iso_date_string_rejects_invalid(value: str) -> None:  # noqa: D103
    with pytest.raises(InvariantViolationError):
        is_iso_date_string(value)


# --- is_iso_utc_date_string ---------------------------------------------------


@allure.epic(EPIC)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.feature(FEATURE)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.tag("predicate", "is_iso_utc_date_string", "happy-path")  # type: ignore[no-untyped-call,untyped-decorator]
@allure.severity(allure.severity_level.NORMAL)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.label("layer", LAYER)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.title("is_iso_utc_date_string accepts UTC-qualified timestamps")  # type: ignore[no-untyped-call,untyped-decorator]
@pytest.mark.parametrize(
    "value",
    ["2025-12-18T10:30:00+00:00", "2025-12-18T10:30:00Z"],
)
def test_is_iso_utc_date_string_accepts_utc(value: str) -> None:  # noqa: D103
    is_iso_utc_date_string(value)  # should not raise


@allure.epic(EPIC)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.feature(FEATURE)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.tag("predicate", "is_iso_utc_date_string", "error")  # type: ignore[no-untyped-call,untyped-decorator]
@allure.severity(allure.severity_level.NORMAL)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.label("layer", LAYER)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.title("is_iso_utc_date_string rejects non-UTC, naive and invalid input")  # type: ignore[no-untyped-call,untyped-decorator]
@pytest.mark.parametrize(
    "value",
    [
        "2025-12-18T10:30:00+02:00",  # valid ISO but not UTC
        "2025-12-18",  # naive (no timezone)
        "nope",  # not a date at all
    ],
)
def test_is_iso_utc_date_string_rejects_invalid(value: str) -> None:  # noqa: D103
    with pytest.raises(InvariantViolationError):
        is_iso_utc_date_string(value)


# --- is_file / is_dir ---------------------------------------------------------


@allure.epic(EPIC)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.feature(FEATURE)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.tag("predicate", "is_file")  # type: ignore[no-untyped-call,untyped-decorator]
@allure.severity(allure.severity_level.NORMAL)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.label("layer", LAYER)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.title("is_file accepts a real file and rejects dirs and missing paths")  # type: ignore[no-untyped-call,untyped-decorator]
def test_is_file(tmp_path: Path) -> None:  # noqa: D103
    a_file = tmp_path / "report.txt"
    a_file.write_text("content")

    is_file(a_file)  # should not raise

    with pytest.raises(InvariantViolationError):
        is_file(tmp_path)  # a directory is not a file
    with pytest.raises(InvariantViolationError):
        is_file(tmp_path / "does_not_exist.txt")


@allure.epic(EPIC)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.feature(FEATURE)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.tag("predicate", "is_dir")  # type: ignore[no-untyped-call,untyped-decorator]
@allure.severity(allure.severity_level.NORMAL)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.label("layer", LAYER)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.title("is_dir accepts a real directory and rejects files and missing paths")  # type: ignore[no-untyped-call,untyped-decorator]
def test_is_dir(tmp_path: Path) -> None:  # noqa: D103
    a_file = tmp_path / "report.txt"
    a_file.write_text("content")

    is_dir(tmp_path)  # should not raise

    with pytest.raises(InvariantViolationError):
        is_dir(a_file)  # a file is not a directory
    with pytest.raises(InvariantViolationError):
        is_dir(tmp_path / "missing")
