# pylint: disable=unsubscriptable-object
# unsubscriptable-object clashes with type hints
from __future__ import annotations

from dataclasses import _MISSING_TYPE, MISSING, Field, field
from typing import TYPE_CHECKING, Optional, TypeVar, Union, cast

_T = TypeVar("_T")


def make_field(default: Union[_T, _MISSING_TYPE]) -> Field[_T]:
    if TYPE_CHECKING:  # pragma: no cover
        return cast(Field[_T], field(default=default))
    return field(default=default)


def rename(
    f: Optional[Field[_T]] = None,
    default: Union[_T, _MISSING_TYPE] = MISSING,
    name: Optional[str] = None,
    ns: Optional[str] = None,
) -> Field[_T]:
    if f is None:
        f = make_field(default=default)
    metadata = dict(f.metadata)
    if name:
        metadata["xml:name"] = name
    if ns:
        metadata["xml:ns"] = ns
    f.metadata = metadata
    return f


def text(
    f: Optional[Field[_T]] = None, default: Union[_T, _MISSING_TYPE] = MISSING
) -> Field[_T]:
    if f is None:
        f = make_field(default=default)
    metadata = dict(f.metadata)
    metadata["xml:text"] = True
    f.metadata = metadata
    return f
