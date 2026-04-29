"""Typed environment variable accessor with key autocompletion support.

Provides a generic, type-safe interface for accessing environment variables,
with IDE autocompletion and mypy validation on keys.

Keys are defined as Literal types in the consuming project, giving full
static analysis support without any runtime overhead.

Example:
    >>> import os
    >>> from typing import Literal
    >>> from types import MappingProxyType
    >>>
    >>> type MyCredKeys = Literal["intranet", "api_service"]
    >>> type MyValueKeys = Literal["expected_fullname"]
    >>>
    >>> def _creds(login_key: str, password_key: str) -> ImmutableCredentials:
    ...     return MappingProxyType({
    ...         "login": os.environ[login_key],
    ...         "password": os.environ[password_key],
    ...     })
    >>>
    >>> def create_env_getters() -> EnvGetters[MyCredKeys, MyValueKeys]:
    ...     return EnvGetters(
    ...         credentials={
    ...             "intranet": _creds("INTRANET_LOGIN", "INTRANET_PASSWORD"),
    ...             "api_service": _creds("API_LOGIN", "API_PASSWORD"),
    ...         },
    ...         values={
    ...             "expected_fullname": os.environ["EXPECTED_FULLNAME"],
    ...         },
    ...     )
    >>>
    >>> env = create_env_getters()
    >>> env.get_credentials("intranet")     # ✅ autocomplete + mypy OK
    >>> env.get_credentials("unknown")      # ❌ mypy error
    >>> env.get_value("expected_fullname")  # ✅ autocomplete + mypy OK
    >>> env.get_value("typo")               # ❌ mypy error

"""

from types import MappingProxyType
from typing import Literal

ImmutableCredentialsKeys = Literal["login", "password"]
type ImmutableCredentials = MappingProxyType[ImmutableCredentialsKeys, str]
"""Read-only credential mapping. Prevents accidental mutation after retrieval."""


class EnvGetters[TCredKeys: str, TValueKeys: str]:
    """Type-safe accessor for environment variables.

    Generic over TCredKeys and TValueKeys — both are inferred from the
    dicts passed at construction, no manual annotation needed when using
    a factory function that declares the return type explicitly.

    Args:
        credentials: Mapping of credential keys to immutable credential pairs.
        values: Mapping of value keys to string values. Optional.

    """

    def __init__(
        self,
        credentials: dict[TCredKeys, ImmutableCredentials] | None = None,
        values: dict[TValueKeys, str] | None = None,
    ) -> None:
        """Initialize the env getter.

        Args:
            credentials: Mapping of credential keys to immutable credential pairs.
                         Keys become the valid arguments for get_credentials().
            values: Mapping of value keys to string values.
                    Keys become the valid arguments for get_value().
                    Defaults to empty dict if not provided.

        """
        self._credentials: dict[TCredKeys, ImmutableCredentials] = credentials or {}
        self._values: dict[TValueKeys, str] = values or {}

    def get_credentials(self, k: TCredKeys) -> ImmutableCredentials:
        """Return the immutable credentials for the given key."""
        return self._credentials[k]

    def get_value(self, k: TValueKeys) -> str:
        """Return the string value for the given key."""
        return self._values[k]
