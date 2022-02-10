# pylint: disable=unsubscriptable-object
from __future__ import annotations

from dataclasses import _MISSING_TYPE, MISSING, Field, field
from typing import TYPE_CHECKING, Optional, TypeVar, Union, cast

_T = TypeVar("_T")


def make_field(default: Union[_T, _MISSING_TYPE]) -> Field[_T]:
    if TYPE_CHECKING:  # pragma: no cover
        return cast(Field[_T], field(default=default))
    return field(default=default)


# NOTE: Actual return type is 'Field[_T]', but we want to help type checkers
# to understand the magic that happens at runtime.
# see https://github.com/python/typeshed/blob/master/stdlib/3.7/dataclasses.pyi
def rename(
    f: Optional[Field[_T]] = None,
    default: Union[_T, _MISSING_TYPE] = MISSING,
    name: Optional[str] = None,
    ns: Optional[str] = None,
) -> _T:
    if f is None:
        f = make_field(default=default)
    metadata = dict(f.metadata)
    if name:
        metadata["xml:name"] = name
    if ns:
        metadata["xml:ns"] = ns
    f.metadata = metadata  # type: ignore[assignment]
    return f  # type: ignore[return-value]


# NOTE: Actual return type is 'Field[_T]', but we want to help type checkers
# to understand the magic that happens at runtime.
# see https://github.com/python/typeshed/blob/master/stdlib/3.7/dataclasses.pyi
def text(
    f: Optional[Field[_T]] = None, default: Union[_T, _MISSING_TYPE] = MISSING
) -> _T:
    if f is None:
        f = make_field(default=default)
    metadata = dict(f.metadata)
    metadata["xml:text"] = True
    f.metadata = metadata  # type: ignore[assignment]
    return f  # type: ignore[return-value]


# NOTE: Actual return type is 'Field[_T]', but we want to help type checkers
# to understand the magic that happens at runtime.
# see https://github.com/python/typeshed/blob/master/stdlib/3.7/dataclasses.pyi
def ignored() -> _T:
    return field(init=False, compare=False)  # type: ignore[no-any-return]
