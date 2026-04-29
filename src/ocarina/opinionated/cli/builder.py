"""CliBuilder — declarative argparse-based CLI builder."""

import sys
from argparse import ArgumentDefaultsHelpFormatter, ArgumentParser, Namespace
from collections.abc import Callable
from typing import TYPE_CHECKING, Any, Final, Never

if TYPE_CHECKING:
    from ocarina.custom_types.effect import Effect

type ArgValidator = Callable[[Any], None]
"""Raises if the value is invalid."""

_INVALID_CLI_ARGUMENTS: Final[str] = "INVALID CLI ARGUMENTS"


def _ucfirst(s: str) -> str:
    return s[:1].upper() + s[1:]


class _SilentArgumentParser(ArgumentParser):
    def error(self, message: str) -> Never:
        """Raise an error."""
        raise ValueError(message)


class CliArg:
    """Declaration of a single CLI argument with optional validation."""

    def __init__(
        self,
        *flags: str,
        validate: ArgValidator | None = None,
        **argparse_kwargs: Any,  # noqa: ANN401
    ) -> None:
        """Initialize the Arg."""
        self.flags = flags
        self.validate = validate
        self.argparse_kwargs = argparse_kwargs


class CliBuilder:
    """Declarative CLI builder on top of argparse.

    The user declares args + validators up front.
    parse() handles parsing, validation, error accumulation, and sys.exit(2).
    """

    def __init__(
        self,
        *,
        args: list[CliArg],
        effects_factory: Callable[[Namespace], tuple[Effect, ...]],
        effects_fail_fast: bool = False,
        description: str = "",
    ) -> None:
        """Build a CLI."""
        self._args = args
        self._effects_factory = effects_factory
        self._effects_fail_fast = effects_fail_fast
        self._description = description

    def parse(self) -> Namespace:
        """Arg parser."""
        parser = _SilentArgumentParser(
            description=self._description,
            formatter_class=ArgumentDefaultsHelpFormatter,
        )
        for arg in self._args:
            parser.add_argument(*arg.flags, **arg.argparse_kwargs)

        try:
            namespace = parser.parse_args()
        except ValueError as exc:
            print(_INVALID_CLI_ARGUMENTS, file=sys.stderr)  # noqa: T201
            print(f"🚫  {_ucfirst(str(exc))}", file=sys.stderr)  # noqa: T201
            parser.print_help(file=sys.stderr)
            sys.exit(2)

        errors: list[str] = []

        for arg in self._args:
            if arg.validate is None:
                continue
            dest = arg.argparse_kwargs.get("dest") or arg.flags[-1].lstrip("-").replace(
                "-", "_"
            )
            value = getattr(namespace, dest)
            try:
                arg.validate(value)
            except Exception as exc:  # noqa: BLE001
                errors.append(str(exc))

        for effect in self._effects_factory(namespace):
            try:
                effect()
            except Exception as exc:  # noqa: BLE001
                errors.append(str(exc))
                if self._effects_fail_fast:
                    break

        if errors:
            print(_INVALID_CLI_ARGUMENTS, file=sys.stderr)  # noqa: T201
            for err in errors:
                print(f"🚫  {_ucfirst(str(err))}", file=sys.stderr)  # noqa: T201
            parser.print_help(file=sys.stderr)
            sys.exit(2)

        return namespace
