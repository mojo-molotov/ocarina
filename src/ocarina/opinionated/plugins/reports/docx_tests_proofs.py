"""Generate test proof documents in DOCX format.

Transforms text log files from automated tests into formatted Word documents,
including screenshots.

Architecture:
    - Recursive reading of log tree (campaigns > suites > cases)
    - UTC metadata parsing and local time conversion
    - Automatic screenshot detection and insertion
    - Robust error handling with logging

Output format:
    - Heading 1: Test campaign
    - Heading 2: Test suite
    - Heading 3: Test case
    - Body: Logs with inserted screenshots

Example:
    >>> generate_docx_proof(
    ...     logs_root=Path("logs/e2e"),
    ...     docx_root=Path(".docx_test_proofs_xxx"),
    ...     logger=logger,
    ... )

"""

import re
import uuid
from contextlib import suppress
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, TypedDict, final

from docx import Document
from docx.enum.text import WD_PARAGRAPH_ALIGNMENT
from docx.shared import Inches

if TYPE_CHECKING:
    from collections.abc import Iterator

    from docx.document import Document as DocxDocument

    from ocarina.ports.ilogger import ILogger

_DEFAULT_SCREENSHOT_NEEDLE = "Screenshot: "
_DEFAULT_UTC_DATE_REGEX = re.compile(r"\[UTC_DATE::([^]]+)]")


def _replace_utc_date(line: str, *, utc_date_regex: re.Pattern[str]) -> str:
    def _repl(m: re.Match[str]) -> str:
        with suppress(Exception):
            return (
                datetime.fromisoformat(m.group(1).replace("Z", "+00:00"))  # noqa: FURB162
                .astimezone()
                .strftime("[%m/%d/%Y | %Hh%M:%S.%f]")
            )
        return m.group(0)

    return utc_date_regex.sub(_repl, line)


def _shorten_docx_path(docx_path: Path) -> Path:
    """Return a short unique path if stem exceeds 8 chars, otherwise unchanged.

    Raises:
        RuntimeError: If a unique filename cannot be generated after 500 attempts.

    """
    max_stem_length = 8
    retries = 500

    if len(docx_path.stem) <= max_stem_length:
        return docx_path

    parent = docx_path.parent
    for _ in range(retries):
        short_name = uuid.uuid4().hex[:max_stem_length]
        new_path = parent / f"{short_name}.docx"
        if not new_path.exists():
            return new_path

    msg = (  # pragma: no cover
        f"Cannot generate a unique short filename for:"
        " "
        f"{docx_path} after {retries} attempts."
    )
    raise RuntimeError(msg)  # pragma: no cover


def _create_unique_output_dir(output_root: Path) -> Path:
    """Create a uniquely named subdirectory (4-char hex) inside output_root.

    Raises:
        RuntimeError: If a unique directory cannot be created after 500 attempts.

    """
    retries = 500

    for _ in range(retries):
        candidate = output_root / uuid.uuid4().hex[:4]
        try:
            candidate.mkdir(parents=True, exist_ok=False)
        except FileExistsError:
            continue
        else:
            return candidate

    msg = (
        "Cannot generate a unique output subdirectory under:"
        " "
        f"{output_root} after {retries} attempts."
    )
    raise RuntimeError(msg)


class _TestCaseEntry(TypedDict):
    test_campaign_name: str
    test_suite_name: str
    test_case_name: str
    file_path: Path


def _safe_iter_lines(file_path: Path, logger: ILogger) -> Iterator[str]:
    try:
        with file_path.open("r", encoding="utf-8", errors="replace") as f:
            yield from f
    except Exception as exc:
        msg = f"Cannot read: {file_path}"
        logger.exception(msg, exc=exc)


def _save_docx(*, doc: DocxDocument, docx_path: Path, logger: ILogger) -> None:
    try:
        doc.save(str(docx_path))
        logger.success(f"Successfully written: {docx_path}")
    except Exception as exc:
        msg = f"Cannot save file: {docx_path}"
        logger.exception(msg, exc=exc)


@final
class _DocxProofGenerator:
    """Generate DOCX test proofs from log files.

    Expected log tree:
        logs_root/
        ├── campaign_1/
        │   ├── suite_A/
        │   │   ├── test_case_1.log
        │   │   └── test_case_2.log
        │   └── suite_B/
        │       └── test_case_3.log
        └── campaign_2/
            └── ...
    """

    def __init__(
        self,
        *,
        logs_root: Path,
        docx_root: Path,
        screenshot_needle: str = _DEFAULT_SCREENSHOT_NEEDLE,
        utc_date_regex: re.Pattern[str] = _DEFAULT_UTC_DATE_REGEX,
    ) -> None:
        self.logs_root = logs_root
        self.docx_root = docx_root
        self._screenshot_needle = screenshot_needle
        self._utc_date_regex = utc_date_regex

    def _iter_test_cases(self, logger: ILogger) -> Iterator[_TestCaseEntry]:
        try:
            for campaign_dir in self.logs_root.iterdir():
                if not campaign_dir.is_dir():
                    continue

                for suite_dir in campaign_dir.iterdir():
                    if not suite_dir.is_dir():
                        continue

                    for file in suite_dir.iterdir():
                        if file.is_file():
                            yield _TestCaseEntry(
                                test_campaign_name=campaign_dir.name,
                                test_suite_name=suite_dir.name,
                                test_case_name=file.stem,
                                file_path=file,
                            )
        except OSError as exc:
            msg = f"Failed to iterate over: {self.logs_root}"
            logger.exception(msg, exc=exc)

    def _create_docx_from_case(
        self, test_case: _TestCaseEntry, logger: ILogger
    ) -> bool:
        campaign_name = test_case["test_campaign_name"]
        suite_name = test_case["test_suite_name"]
        case_name = test_case["test_case_name"]
        file_path = test_case["file_path"]

        doc = Document()
        doc.add_heading(
            campaign_name, level=1
        ).alignment = WD_PARAGRAPH_ALIGNMENT.CENTER
        doc.add_heading(suite_name, level=2).alignment = WD_PARAGRAPH_ALIGNMENT.CENTER
        doc.add_paragraph()
        doc.add_heading(case_name, level=3)

        for line in _safe_iter_lines(file_path, logger):
            normalized_line = _replace_utc_date(
                line.rstrip("\n"), utc_date_regex=self._utc_date_regex
            )

            if self._screenshot_needle in normalized_line:
                parts = normalized_line.split(self._screenshot_needle, 1)
                if len(parts) > 1 and parts[1].strip():
                    image_path = Path(parts[1].strip())
                    if image_path.exists() and image_path.is_file():
                        doc.add_paragraph()
                        try:
                            doc.add_picture(str(image_path), width=Inches(6))
                        except Exception as exc:
                            msg = f"Cannot add image {image_path}"
                            logger.exception(msg, exc=exc)
            else:
                p = doc.add_paragraph()
                p.paragraph_format.space_before = 0
                p.paragraph_format.space_after = 0
                p.add_run(normalized_line)

        relative_path = file_path.relative_to(self.logs_root)
        docx_path = (self.docx_root / relative_path).with_suffix(".docx").resolve()

        try:
            docx_path.parent.mkdir(parents=True, exist_ok=True)
            doc.save(str(docx_path))
        except FileNotFoundError, OSError:
            original_docx_path = docx_path
            docx_path = _shorten_docx_path(docx_path)
            msg = (
                f"Filename too long or access error for: {original_docx_path}."
                f" Retrying with: {docx_path}"
            )
            logger.warning(msg)
            _save_docx(docx_path=docx_path, doc=doc, logger=logger)
            return True
        else:
            return True

    def generate_docx_proofs(self, logger: ILogger) -> int:
        return sum(
            self._create_docx_from_case(case, logger)
            for case in self._iter_test_cases(logger)
        )


def generate_docx_proof(  # noqa: PLR0913
    *,
    logs_root: Path,
    output_root: Path,
    logger: ILogger,
    screenshot_needle: str = _DEFAULT_SCREENSHOT_NEEDLE,
    utc_date_regex: re.Pattern[str] = _DEFAULT_UTC_DATE_REGEX,
    auto_create_unique_directory: bool = True,
) -> None:
    """Generate DOCX test proofs from log files.

    Args:
        logs_root: Root directory of the log tree to process.
        output_root: Root directory where DOCX files will be written.
        logger: Logger for progress and error reporting.
        screenshot_needle: used to detect screenshot lines. Default: "Screenshot: ".
        utc_date_regex: used to detect and replace UTC dates. Default: [UTC_DATE::...].
        auto_create_unique_directory: creates automatically a random-named unique dir.

    """
    if not logs_root.is_dir():
        msg = f"Directory not accessible: {logs_root}. Generation skipped."
        logger.warning(msg)
        return

    docx_root = (
        _create_unique_output_dir(output_root)
        if auto_create_unique_directory
        else output_root
    )

    generated_count = _DocxProofGenerator(
        logs_root=logs_root,
        docx_root=docx_root,
        screenshot_needle=screenshot_needle,
        utc_date_regex=utc_date_regex,
    ).generate_docx_proofs(logger)

    if generated_count == 0:
        msg = f"No test case found under: {logs_root}. Nothing was generated."
        logger.warning(msg)
        if auto_create_unique_directory:
            with suppress(Exception):
                docx_root.rmdir()
        return

    msg = (
        f"Plugin execution done. Generated {generated_count} DOCX. Output: {docx_root}"
    )
    logger.info(msg)
