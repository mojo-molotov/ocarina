"""Campaign validation errors.

Defines exceptions for test campaign invariant violations, such as
duplicate test names within a campaign.

Exception hierarchy:
    InvariantViolationError → DuplicatesError → DuplicateTestNameError

Example:
    >>> campaign = TestCampaign(tests=[
    ...     Test(name="login_test", ...),
    ...     Test(name="login_test", ...),  # Duplicate!
    ... ])
    DuplicateTestNameError: Duplicate test names detected in TestCampaign:
     - login_test

"""

from typing import TYPE_CHECKING, final

from ocarina.dsl.invariants.errors import DuplicatesError

if TYPE_CHECKING:
    from collections.abc import Sequence


@final
class DuplicateTestNameError(DuplicatesError):
    """Raised when duplicate test names are detected in a campaign.

    Test campaigns require unique test names for identification and reporting.

    Attributes:
        duplicates: Sequence of duplicate test names found.

    Example:
        >>> duplicates = ["login_test", "setup_test"]
        >>> raise DuplicateTestNameError(duplicates)

    """

    def __init__(self, duplicates: Sequence[str]) -> None:
        """Initialize with duplicate test names.

        Args:
            duplicates: Test names appearing more than once in the campaign.

        """
        message = "Duplicate test names detected in TestCampaign:\n" + "\n".join(
            f" - {name}" for name in duplicates
        )
        super().__init__(duplicates=duplicates, message=message)
