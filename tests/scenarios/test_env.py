"""EnvGetters: type-safe env-var accessor for credentials and values."""

# ruff: noqa: S101

from types import MappingProxyType
from typing import Literal, Never

import allure
import pytest

from ocarina.opinionated.infra.env import EnvGetters, ImmutableCredentials

EPIC = "EnvGetters"
FEATURE = "Env getters"
LAYER = "unit"


def _creds(login: str, password: str) -> ImmutableCredentials:
    return MappingProxyType({"login": login, "password": password})


@allure.epic(EPIC)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.feature(FEATURE)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.tag("env", "credentials")  # type: ignore[no-untyped-call,untyped-decorator]
@allure.severity(allure.severity_level.NORMAL)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.label("layer", LAYER)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.title("get_credentials returns the mapping for a known key and is immutable")  # type: ignore[no-untyped-call,untyped-decorator]
def test_get_credentials_returns_immutable_mapping() -> None:  # noqa: D103
    env = EnvGetters[Literal["intranet"], Never](
        credentials={"intranet": _creds("alice", "s3cret")},
    )

    creds = env.get_credentials("intranet")

    assert creds["login"] == "alice"
    assert creds["password"] == "s3cret"  # noqa: S105
    with pytest.raises(TypeError):
        creds["login"] = "mallory"  # type: ignore[index]


@allure.epic(EPIC)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.feature(FEATURE)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.tag("env", "values")  # type: ignore[no-untyped-call,untyped-decorator]
@allure.severity(allure.severity_level.MINOR)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.label("layer", LAYER)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.title("get_value returns the string for a known key")  # type: ignore[no-untyped-call,untyped-decorator]
def test_get_value_returns_string() -> None:  # noqa: D103
    env = EnvGetters[Never, Literal["expected_fullname"]](
        values={"expected_fullname": "Alice Alpha"}
    )

    assert env.get_value("expected_fullname") == "Alice Alpha"


@allure.epic(EPIC)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.feature(FEATURE)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.tag("env", "error")  # type: ignore[no-untyped-call,untyped-decorator]
@allure.severity(allure.severity_level.NORMAL)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.label("layer", LAYER)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.title("Unknown keys raise KeyError on both getters")  # type: ignore[no-untyped-call,untyped-decorator]
def test_unknown_keys_raise_keyerror() -> None:  # noqa: D103
    env = EnvGetters(
        credentials={"intranet": _creds("u", "p")},
        values={"name": "bob"},
    )

    with pytest.raises(KeyError):
        env.get_credentials("ghost")
    with pytest.raises(KeyError):
        env.get_value("ghost")


@allure.epic(EPIC)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.feature(FEATURE)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.tag("env", "defaults")  # type: ignore[no-untyped-call,untyped-decorator]
@allure.severity(allure.severity_level.MINOR)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.label("layer", LAYER)  # type: ignore[no-untyped-call,untyped-decorator]
@allure.title("Default construction yields empty maps; every lookup is a KeyError")  # type: ignore[no-untyped-call,untyped-decorator]
def test_default_construction_is_empty() -> None:  # noqa: D103
    env: EnvGetters[str, str] = EnvGetters()

    with pytest.raises(KeyError):
        env.get_credentials("anything")
    with pytest.raises(KeyError):
        env.get_value("anything")
