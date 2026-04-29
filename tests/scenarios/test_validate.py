"""validate() DSL: fluent assertion chains with alternatives and type-shifting."""

# ruff: noqa: S101

import allure
import pytest

from ocarina.dsl.invariants.assertions import (
    is_email,
    is_equal_to,
    is_not_none,
    is_positive,
    is_str,
)
from ocarina.dsl.invariants.errors import AggregateInvariantViolationError
from ocarina.dsl.invariants.internals.validation_chain import chain_validations
from ocarina.dsl.invariants.validate import validate

EPIC = "validate()"
FEATURE = "Validation DSL"
LAYER = "unit"


@allure.epic(EPIC)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.feature(FEATURE)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.tag("validate", "happy-path")  # type: ignore[no-untyped-call,untyped-decorator]
@allure.severity(allure.severity_level.CRITICAL)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.label("layer", LAYER)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.title("A passing chain's raise_if_invalid is a no-op")  # type: ignore[no-untyped-call,untyped-decorator]
def test_passing_chain_does_not_raise() -> None:  # noqa: D103
    # Should not raise
    validate(42, name="n").assert_that(is_positive).execute().raise_if_invalid()
    validate("a@b.com", name="email").assert_that(is_str).assert_that(
        is_email
    ).execute().raise_if_invalid()


@allure.epic(EPIC)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.feature(FEATURE)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.tag("validate", "error-aggregation")  # type: ignore[no-untyped-call,untyped-decorator]
@allure.severity(allure.severity_level.CRITICAL)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.label("layer", LAYER)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.title(  # type: ignore[no-untyped-call,untyped-decorator]
    "A failing chain raises AggregateInvariantViolationError with all collected errors"
)
def test_failing_chain_raises_with_all_errors() -> None:  # noqa: D103
    with pytest.raises(AggregateInvariantViolationError) as exc_info:
        validate(-1, name="n").assert_that(is_positive).assert_that(
            is_equal_to(10)
        ).execute().raise_if_invalid()

    # Both failures were collected, not just the first
    assert len(exc_info.value.errors) == 2  # noqa: PLR2004


@allure.epic(EPIC)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.feature(FEATURE)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.tag("validate", "otherwise")  # type: ignore[no-untyped-call,untyped-decorator]
@allure.severity(allure.severity_level.NORMAL)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.label("layer", LAYER)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.title(  # type: ignore[no-untyped-call,untyped-decorator]
    "otherwise acts as logical OR: alternative predicate rescues a failing primary"
)
def test_otherwise_rescues_failing_primary() -> None:  # noqa: D103
    # 20 is not equal to 18, but it is positive → overall valid
    validate(20, name="age").assert_that(is_equal_to(18)).otherwise(
        is_positive
    ).execute().raise_if_invalid()

    # If both fail, the chain fails
    with pytest.raises(AggregateInvariantViolationError):
        validate(-5, name="age").assert_that(is_equal_to(18)).otherwise(
            is_positive
        ).execute().raise_if_invalid()


@allure.epic(EPIC)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.feature(FEATURE)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.tag("validate", "then")  # type: ignore[no-untyped-call,untyped-decorator]
@allure.severity(allure.severity_level.NORMAL)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.label("layer", LAYER)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.title("then shifts validation focus to a new value while preserving the chain")  # type: ignore[no-untyped-call,untyped-decorator]
def test_then_shifts_focus_to_new_value() -> None:  # noqa: D103
    validate(42, name="n").assert_that(is_positive).then(
        "a@b.com", name="email"
    ).assert_that(is_str).assert_that(is_email).execute().raise_if_invalid()

    # A failure on the second value surfaces in the aggregate
    with pytest.raises(AggregateInvariantViolationError):
        validate(42).assert_that(is_positive).then("not-an-email").assert_that(
            is_email
        ).execute().raise_if_invalid()


@allure.epic(EPIC)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.feature(FEATURE)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.tag("validate", "chain")  # type: ignore[no-untyped-call,untyped-decorator]
@allure.severity(allure.severity_level.NORMAL)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.label("layer", LAYER)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.title("chain_validations merges independent chains and aggregates their errors")  # type: ignore[no-untyped-call,untyped-decorator]
def test_chain_validations_merges_errors() -> None:  # noqa: D103
    chain_a = validate(-1, name="a").assert_that(is_positive)
    chain_b = validate(None, name="b").assert_that(is_not_none)

    with pytest.raises(AggregateInvariantViolationError) as exc_info:
        chain_validations(chain_a, chain_b).execute().raise_if_invalid()

    assert len(exc_info.value.errors) == 2  # noqa: PLR2004


@allure.epic(EPIC)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.feature(FEATURE)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.tag("validate", "messages")  # type: ignore[no-untyped-call,untyped-decorator]
@allure.severity(allure.severity_level.MINOR)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.label("layer", LAYER)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.title("Custom error messages propagate through the aggregate exception")  # type: ignore[no-untyped-call,untyped-decorator]
def test_custom_error_message_surfaces() -> None:  # noqa: D103
    with pytest.raises(AggregateInvariantViolationError) as exc_info:
        validate(-1, name="age").assert_that(
            is_positive, msg="age must be positive"
        ).execute().raise_if_invalid()

    assert any("age must be positive" in str(e) for e in exc_info.value.errors)
