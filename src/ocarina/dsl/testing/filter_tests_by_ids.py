"""Filter a sequence of tests by their test_id.

Designed to be fed from CLI flags --only / --exclude. The two are mutually
exclusive — passing both raises.

Unknown IDs (not matching any test.test_id) are silently ignored, so a typo
in a CI script does not break the run.
"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Iterable, Sequence

    from ocarina.dsl.testing.oc_test import Test
    from ocarina.ports.ilogger import ILogger


def filter_tests_by_ids[Driver](
    tests: Sequence[Test[Driver]],
    *,
    only: Iterable[str] = (),
    exclude: Iterable[str] = (),
    logger: ILogger,
) -> Sequence[Test[Driver]]:
    """Return tests filtered by test_id.

    Args:
        tests: The full list of tests to filter.
        only: If non-empty, keep only tests whose test_id is in this set.
        exclude: If non-empty, drop tests whose test_id is in this set.
        logger: Used to log matched IDs.

    Raises:
        ValueError: If both ``only`` and ``exclude`` are non-empty.

    """
    only_set = set(only)
    exclude_set = set(exclude)

    if only_set and exclude_set:
        msg = "--only and --exclude cannot be used together"
        raise ValueError(msg)

    known_ids = {test.test_id for test in tests}

    if only_set:
        matched = only_set & known_ids
        if matched:
            joined = ", ".join(sorted(matched))
            msg = f"--only: matched test IDs: {joined}"
            logger.info(msg)
        return [test for test in tests if test.test_id in only_set]

    if exclude_set:
        matched = exclude_set & known_ids
        if matched:
            joined = ", ".join(sorted(matched))
            msg = f"--exclude: matched test IDs: {joined}"
            logger.info(msg)
        return [test for test in tests if test.test_id not in exclude_set]

    return tests
