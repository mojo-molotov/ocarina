"""Property-based tests for the invariants DSL.

Each test states a law about an assertion or about the validation chain, then
lets Hypothesis generate thousands of inputs looking for a counter-example.
No hand-picked examples: the whole point is to let the machine probe the
space.
"""

# ruff: noqa: S101

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import allure
from hypothesis import given
from hypothesis import strategies as st

from ocarina.dsl.invariants.assertions import (
    has_unique_elements,
    is_empty,
    is_equal_to,
    is_in,
    is_less_than_or_equal_to,
    is_none,
    is_not_none,
    is_not_zero,
    is_positive,
    is_str,
    is_truthy,
)
from ocarina.dsl.invariants.errors import (
    AggregateInvariantViolationError,
    InvariantViolationError,
)
from ocarina.dsl.invariants.validate import validate

if TYPE_CHECKING:
    from collections.abc import Callable

EPIC = "Invariants DSL (PBT)"
FEATURE = "Invariants (PBT)"
LAYER = "unit"


def _raises(predicate: Callable[[Any], None], value: Any) -> bool:  # noqa: ANN401
    try:
        predicate(value)
    except InvariantViolationError:
        return True
    return False


# --- Atomic predicates: each one is a total function of its input -------------


@allure.epic(EPIC)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.feature(FEATURE)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.tag("pbt", "predicate", "is_positive")  # type: ignore[no-untyped-call,untyped-decorator]
@allure.severity(allure.severity_level.NORMAL)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.label("layer", LAYER)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.title("is_positive raises iff n is strictly negative")  # type: ignore[no-untyped-call,untyped-decorator]
@given(st.integers())
def test_is_positive_agrees_with_gte_zero(n: int) -> None:  # noqa: D103
    assert _raises(is_positive, n) == (n < 0)


@allure.epic(EPIC)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.feature(FEATURE)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.tag("pbt", "predicate", "is_not_zero")  # type: ignore[no-untyped-call,untyped-decorator]
@allure.severity(allure.severity_level.NORMAL)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.label("layer", LAYER)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.title("is_not_zero raises iff n equals zero")  # type: ignore[no-untyped-call,untyped-decorator]
@given(st.integers())
def test_is_not_zero_agrees_with_nonzero(n: int) -> None:  # noqa: D103
    assert _raises(is_not_zero, n) == (n == 0)


@allure.epic(EPIC)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.feature(FEATURE)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.tag("pbt", "predicate", "is_equal_to")  # type: ignore[no-untyped-call,untyped-decorator]
@allure.severity(allure.severity_level.NORMAL)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.label("layer", LAYER)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.title("is_equal_to(a)(b) raises iff a != b")  # type: ignore[no-untyped-call,untyped-decorator]
@given(st.integers(), st.integers())
def test_is_equal_to_agrees_with_equality(a: int, b: int) -> None:  # noqa: D103
    assert _raises(is_equal_to(a), b) == (a != b)


@allure.epic(EPIC)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.feature(FEATURE)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.tag("pbt", "predicate", "is_in")  # type: ignore[no-untyped-call,untyped-decorator]
@allure.severity(allure.severity_level.NORMAL)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.label("layer", LAYER)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.title("is_in(xs)(v) raises iff v not in xs")  # type: ignore[no-untyped-call,untyped-decorator]
@given(st.lists(st.integers(), max_size=20), st.integers())
def test_is_in_agrees_with_membership(xs: list[int], v: int) -> None:  # noqa: D103
    assert _raises(is_in(xs), v) == (v not in xs)


@allure.epic(EPIC)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.feature(FEATURE)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.tag("pbt", "predicate", "is_less_than_or_equal_to")  # type: ignore[no-untyped-call,untyped-decorator]
@allure.severity(allure.severity_level.NORMAL)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.label("layer", LAYER)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.title("is_less_than_or_equal_to(a)(b) raises iff b > a")  # type: ignore[no-untyped-call,untyped-decorator]
@given(st.integers(), st.integers())
def test_is_lte_agrees_with_lte_operator(a: int, b: int) -> None:  # noqa: D103
    assert _raises(is_less_than_or_equal_to(a), b) == (b > a)


@allure.epic(EPIC)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.feature(FEATURE)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.tag("pbt", "predicate", "is_str")  # type: ignore[no-untyped-call,untyped-decorator]
@allure.severity(allure.severity_level.NORMAL)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.label("layer", LAYER)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.title("is_str raises iff the value is not a string")  # type: ignore[no-untyped-call,untyped-decorator]
@given(
    st.one_of(
        st.text(),
        st.integers(),
        st.floats(allow_nan=False, allow_infinity=False),
        st.booleans(),
        st.none(),
        st.lists(st.integers(), max_size=5),
    )
)
def test_is_str_agrees_with_isinstance(value: Any) -> None:  # noqa: ANN401, D103
    assert _raises(is_str, value) == (not isinstance(value, str))


# A grab-bag of values spanning None, falsy and truthy across several types.
_ANY_VALUE = st.one_of(
    st.none(),
    st.booleans(),
    st.integers(),
    st.floats(allow_nan=False, allow_infinity=False),
    st.text(),
    st.lists(st.integers(), max_size=5),
)


@allure.epic(EPIC)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.feature(FEATURE)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.tag("pbt", "predicate", "is_none")  # type: ignore[no-untyped-call,untyped-decorator]
@allure.severity(allure.severity_level.NORMAL)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.label("layer", LAYER)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.title("is_none raises iff the value is not None")  # type: ignore[no-untyped-call,untyped-decorator]
@given(_ANY_VALUE)
def test_is_none_agrees_with_identity(value: Any) -> None:  # noqa: ANN401, D103
    assert _raises(is_none, value) == (value is not None)


@allure.epic(EPIC)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.feature(FEATURE)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.tag("pbt", "predicate", "is_not_none")  # type: ignore[no-untyped-call,untyped-decorator]
@allure.severity(allure.severity_level.NORMAL)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.label("layer", LAYER)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.title("is_not_none raises iff the value is None")  # type: ignore[no-untyped-call,untyped-decorator]
@given(_ANY_VALUE)
def test_is_not_none_agrees_with_identity(value: Any) -> None:  # noqa: ANN401, D103
    assert _raises(is_not_none, value) == (value is None)


@allure.epic(EPIC)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.feature(FEATURE)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.tag("pbt", "predicate", "is_truthy")  # type: ignore[no-untyped-call,untyped-decorator]
@allure.severity(allure.severity_level.NORMAL)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.label("layer", LAYER)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.title("is_truthy raises iff the value is falsy")  # type: ignore[no-untyped-call,untyped-decorator]
@given(_ANY_VALUE)
def test_is_truthy_agrees_with_bool(value: Any) -> None:  # noqa: ANN401, D103
    assert _raises(is_truthy, value) == (not value)


@allure.epic(EPIC)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.feature(FEATURE)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.tag("pbt", "predicate", "is_empty")  # type: ignore[no-untyped-call,untyped-decorator]
@allure.severity(allure.severity_level.NORMAL)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.label("layer", LAYER)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.title("is_empty raises iff the collection has a non-zero length")  # type: ignore[no-untyped-call,untyped-decorator]
@given(
    st.one_of(
        st.text(),
        st.lists(st.integers(), max_size=10),
        st.dictionaries(st.text(), st.integers(), max_size=5),
    )
)
def test_is_empty_agrees_with_len(value: Any) -> None:  # noqa: ANN401, D103
    assert _raises(is_empty, value) == (len(value) != 0)


@allure.epic(EPIC)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.feature(FEATURE)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.tag("pbt", "predicate", "has_unique_elements")  # type: ignore[no-untyped-call,untyped-decorator]
@allure.severity(allure.severity_level.NORMAL)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.label("layer", LAYER)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.title("has_unique_elements raises iff the list holds a repeated value")  # type: ignore[no-untyped-call,untyped-decorator]
@given(st.lists(st.integers(), max_size=20))
def test_has_unique_elements_agrees_with_set(xs: list[int]) -> None:  # noqa: D103
    assert _raises(has_unique_elements(), xs) == (len(set(xs)) != len(xs))


# --- Composite laws about the validation chain --------------------------------


# A menu of predicates over int — all total, all pure.
_PREDICATE_MENU: list[tuple[str, Callable[[int], None]]] = [
    ("is_positive", is_positive),
    ("is_not_zero", is_not_zero),
    ("is_eq_0", is_equal_to(0)),
    ("is_eq_1", is_equal_to(1)),
    ("is_lte_10", is_less_than_or_equal_to(10)),
]


@allure.epic(EPIC)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.feature(FEATURE)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.tag("pbt", "chain", "aggregation")  # type: ignore[no-untyped-call,untyped-decorator]
@allure.severity(allure.severity_level.CRITICAL)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.label("layer", LAYER)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.title(
    "A validation chain aggregates one error per failing predicate — no more, no less"
)  # type: ignore[no-untyped-call,untyped-decorator]
@given(
    value=st.integers(),
    predicates=st.lists(
        st.sampled_from([p for _, p in _PREDICATE_MENU]),
        min_size=1,
        max_size=6,
    ),
)
def test_chain_aggregates_one_error_per_failing_predicate(  # noqa: D103
    value: int,
    predicates: list[Callable[[int], None]],
) -> None:
    expected_errors = sum(1 for p in predicates if _raises(p, value))

    chain = validate(value, name="n")
    for p in predicates:
        chain = chain.assert_that(p)  # type: ignore[assignment]
    result = chain.execute()  # type: ignore[attr-defined]

    if expected_errors == 0:
        assert result.is_valid
        assert len(result.errors) == 0
    else:
        assert not result.is_valid
        assert len(result.errors) == expected_errors
        try:
            result.raise_if_invalid()
        except AggregateInvariantViolationError as exc:
            assert len(exc.errors) == expected_errors  # noqa: PT017
        else:
            msg = "Expected AggregateInvariantViolationError but nothing was raised"
            raise AssertionError(msg)


@allure.epic(EPIC)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.feature(FEATURE)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.tag("pbt", "otherwise", "logical-or")  # type: ignore[no-untyped-call,untyped-decorator]
@allure.severity(allure.severity_level.CRITICAL)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.label("layer", LAYER)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.title(
    "otherwise implements logical OR — the chain is valid iff P(v) or Q(v) is valid"
)  # type: ignore[no-untyped-call,untyped-decorator]
@given(
    value=st.integers(),
    primary=st.sampled_from([p for _, p in _PREDICATE_MENU]),
    alternative=st.sampled_from([p for _, p in _PREDICATE_MENU]),
)
def test_otherwise_is_logical_or(  # noqa: D103
    value: int,
    primary: Callable[[int], None],
    alternative: Callable[[int], None],
) -> None:
    expected_valid = (not _raises(primary, value)) or (not _raises(alternative, value))

    result = (
        validate(value, name="n").assert_that(primary).otherwise(alternative).execute()
    )

    assert result.is_valid == expected_valid
