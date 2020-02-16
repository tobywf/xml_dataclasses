from dataclasses import dataclass
from itertools import product
from typing import List, Optional, Union, _GenericAlias

import pytest

from xml_dataclasses.exceptions import XmlTypeError
from xml_dataclasses.resolve_types import xml_dataclass

NS = "http://www.w3.org/XML/1998/namespace"


@dataclass
class Dt:
    pass


@xml_dataclass
class XmlDt1:
    __ns__ = NS


@xml_dataclass
class XmlDt2:
    __ns__ = None


@xml_dataclass
class XmlDt3:
    __ns__ = NS


@pytest.mark.parametrize(
    "fn,tp",
    list(
        product(
            [
                lambda tp: tp,
                lambda tp: Optional[tp],
                lambda tp: List[tp],
                lambda tp: Union[tp, str],
            ],
            [int, object, float, Dt],
        )
    )
    + [(lambda tp: List[tp], str)],
)
def test_invalid_field_types_1(fn, tp):
    class Foo:
        __ns__ = None
        bar: fn(tp)

    with pytest.raises(XmlTypeError) as exc_info:
        xml_dataclass(Foo)

    msg = str(exc_info.value)
    assert "Invalid type" in msg
    assert "'bar'" in msg
    cause = exc_info.value.__cause__
    assert isinstance(cause, XmlTypeError)


@pytest.mark.parametrize(
    "tp,err",
    [
        (_GenericAlias(list, (int, str)), "List type has invalid number of arguments"),
        (List[Optional[XmlDt1]], "Nested type cannot be optional"),
        (Optional[List[Optional[XmlDt1]]], "Nested type cannot be optional"),
        (Union[XmlDt1, XmlDt2], "different namespaces"),
    ],
)
def test_invalid_field_types_2(tp, err):
    class Foo:
        __ns__ = None
        bar: tp

    with pytest.raises(XmlTypeError) as exc_info:
        xml_dataclass(Foo)

    msg = str(exc_info.value)
    assert "Invalid type" in msg
    assert "'bar'" in msg
    assert err in msg
    cause = exc_info.value.__cause__
    assert isinstance(cause, XmlTypeError)


@pytest.mark.parametrize(
    "tp, types, is_list, is_optional",
    [
        (XmlDt1, {XmlDt1}, False, False),
        (Optional[XmlDt1], {XmlDt1}, False, True),
        (List[XmlDt1], {XmlDt1}, True, False),
        (Optional[List[XmlDt1]], {XmlDt1}, True, True),
        (Union[XmlDt1, XmlDt3], {XmlDt1, XmlDt3}, False, False),
        (Optional[Union[XmlDt3, XmlDt1]], {XmlDt1, XmlDt3}, False, True),
        (Union[XmlDt1, XmlDt3, None], {XmlDt1, XmlDt3}, False, True),
        (List[Union[XmlDt3, XmlDt1]], {XmlDt1, XmlDt3}, True, False),
        (Optional[List[Union[XmlDt1, XmlDt3]]], {XmlDt1, XmlDt3}, True, True),
    ],
)
def test_valid_field_types_child(tp, types, is_list, is_optional):
    @xml_dataclass
    class Foo:
        __ns__ = None
        bar: tp

    assert not Foo.__attributes__
    assert not Foo.__text_field__
    assert len(Foo.__children__) == 1
    bar = Foo.__children__[0]
    assert bar.dt_name == "bar"
    assert bar.is_optional is is_optional
    assert bar.xml_name == f"{{{NS}}}bar"
    # WARNING: type order is *not* always preserved. this drove me crazy:
    # >>> Optional[List[Union[XmlDt1, XmlDt3]]]
    # typing.Union[typing.List[typing.Union[resolve_types_resolve_test.XmlDt3,
    # resolve_types_resolve_test.XmlDt1]], NoneType]
    assert set(bar.base_types) == types
    assert bar.is_list is is_list
