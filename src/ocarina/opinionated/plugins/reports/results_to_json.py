"""Generate JSON test reports.

Serializes test results into structured, machine-readable JSON files.
Designed for integration with CI/CD pipelines, monitoring tools,
or automated reporting systems.

Output format:
    {
      "Campaign": {
        "Suite": {
          "test_case": [
            {"status": "success" | "fail", "error"?: "..."},
            counter,
            metadata
          ]
        }
      }
    }

Example:
    >>> results_dir = Path(tempfile.mkdtemp(prefix=".json_results_", dir=Path.cwd()))
    >>> generate_json_results(results, results_dir=results_dir, logger=logger)
    # Creates: results_dir/abcd1234.json

"""

import json
import uuid
from typing import TYPE_CHECKING, Any

from ocarina.railway.result import is_fail, is_ok

if TYPE_CHECKING:
    from pathlib import Path

    from ocarina.custom_types.oc_test_layers import TestCycleResults
    from ocarina.ports.ilogger import ILogger


def _result_to_serializable(v: Any) -> dict[str, str]:  # noqa: ANN401
    if is_ok(v):
        return {"status": "success"}
    if is_fail(v):
        return {"status": "fail", "error": str(v.error)}

    msg = f"Expected Ok or Fail instances, but got: {type(v)}"
    raise TypeError(msg)


def generate_json_results(
    *,
    results: TestCycleResults,
    output_dir: Path,
    logger: ILogger,
) -> None:
    """Write test results to a JSON file in results_dir.

    Args:
        results: Hierarchical test results structure.
        output_dir: Directory where the JSON file will be written.
        logger: Logger for progress and error reporting.

    Raises:
        RuntimeError: If a unique filename cannot be generated.

    """
    output_dir.mkdir(parents=True, exist_ok=True)

    max_stem_length = 8
    max_attempts = 500
    for _ in range(max_attempts):
        filename = f"{uuid.uuid4().hex[:max_stem_length]}.json"
        file_path = output_dir / filename

        if not file_path.exists():
            break
    else:
        msg = f"Can't generate unique JSON filename in: {output_dir}."
        raise RuntimeError(msg)

    payload = {
        campaign_name: {
            suite_name: tests for suite_name, tests in suites.items() if tests
        }
        for campaign_name, suites in results.items()
        if any(tests for tests in suites.values())
    }

    if not payload:
        logger.warning("No test results to write.")
        return

    try:
        with file_path.open("w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2, default=_result_to_serializable)
    except Exception as exc:
        msg = f"Can't write JSON file: {file_path}"
        logger.exception(msg, exc=exc)
        return

    msg = f"Plugin execution done. Output: {file_path}"
    logger.info(msg)
