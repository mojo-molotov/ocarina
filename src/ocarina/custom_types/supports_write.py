"""ISO Python stdlib: not exposed type."""

from typing import Protocol, TypeVar

_T_contra = TypeVar("_T_contra", contravariant=True)


class SupportsWrite(Protocol[_T_contra]):  # noqa: D101
    def write(self, s: _T_contra, /) -> object: ...  # noqa: D102
