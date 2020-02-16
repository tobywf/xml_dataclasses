from dataclasses import MISSING, Field, dataclass, fields
from typing import List, Optional, Union
from unittest.mock import Mock

import pytest

from xml_dataclasses.structs import (
    AttrInfo,
    ChildInfo,
    TextInfo,
    XmlDataclass,
    XmlFieldType,
    _check_str_type,
    _xml_field,
    attr,
    child,
    is_xml_dataclass,
    text,
    xml_dataclass,
)

NS = "http://www.w3.org/XML/1998/namespace"


def make_xml_dt(tp, f):
    return type("Foo", (), {"__ns__": None, "__annotations__": {"bar": tp}, "bar": f})


def MockField(tp, name="bar", default=MISSING, metadata=None):
    if not metadata:
        metadata = {}
    mock = Mock(spec_set=Field, type=tp, default=default, metadata=metadata)
    mock.name = name
    return mock


@dataclass
class Dt1:
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


INVALID_STR_TYPES = [
    List[str],
    Optional[List[str]],
    int,
    Optional[int],
    Dt1,
    XmlDt1,
    List[XmlDt1],
]


@pytest.mark.parametrize(
    "cls,result",
    [
        (int, False),
        (str, False),
        (object, False),
        (Dt1, False),
        (XmlDt1, True),
        (XmlDt2, True),
    ],
)
def test_is_xml_dataclass(cls, result):
    assert is_xml_dataclass(cls) is result


@pytest.mark.parametrize("tp,is_opt", [(str, False), (Optional[str], True)])
def test__check_str_type_good_path(tp, is_opt):
    f = MockField(tp=tp)
    assert _check_str_type(f) is is_opt


@pytest.mark.parametrize(
    "type_in",
    [
        int,
        object,
        Dt1,
        XmlDataclass,
        Optional[XmlDataclass],
        List[XmlDataclass],
        Optional[List[XmlDataclass]],
        Union[str, XmlDataclass],
        List[Union[str, XmlDataclass]],
    ],
)
def test__check_str_type_bad_path(type_in):
    f = MockField(tp=type_in)

    with pytest.raises(ValueError):
        _check_str_type(f)


def make_ai(tp_in, f, xml_name, is_req, is_opt):
    cls = make_xml_dt(tp_in, f)
    return (cls, AttrInfo(f, "bar", xml_name, is_req, is_opt))


@pytest.mark.parametrize(
    "cls,info",
    [
        make_ai(str, attr(), "bar", True, False),
        make_ai(str, attr(namespace=NS), f"{{{NS}}}bar", True, False),
        make_ai(str, attr(rename="baz"), "baz", True, False),
        make_ai(str, attr(namespace=NS, rename="baz"), f"{{{NS}}}baz", True, False),
        make_ai(
            Optional[str], attr(default=None, namespace=NS), f"{{{NS}}}bar", False, True
        ),
        make_ai(Optional[str], attr(default=None), "bar", False, True),
        make_ai(
            Optional[str],
            attr(default=None, namespace=NS, rename="baz"),
            f"{{{NS}}}baz",
            False,
            True,
        ),
        make_ai(Optional[str], attr(default=None, rename="baz"), "baz", False, True),
    ],
)
def test_attr_def_good_path(cls, info):
    dt = xml_dataclass(cls)
    assert not dt.__children__
    assert not dt.__text_field__
    assert len(dt.__attributes__) == 1
    bar = dt.__attributes__[0]
    assert bar == info


@pytest.mark.parametrize("tp", INVALID_STR_TYPES)
def test_attr_def_bad_path(tp):
    class Foo:
        __ns__ = None
        bar: tp = attr()

    with pytest.raises(ValueError) as exc_info:
        xml_dataclass(Foo)

    msg = str(exc_info.value)
    assert "Invalid type" in msg
    assert "'bar'" in msg


def make_ti(tp_in, f, is_req, is_opt):
    cls = make_xml_dt(tp_in, f)
    return (cls, TextInfo(f, "bar", is_req, is_opt))


@pytest.mark.parametrize(
    "cls,info",
    [
        make_ti(str, text(), True, False),
        make_ti(str, text(default=""), False, False),
        make_ti(Optional[str], text(default=None), False, True),
    ],
)
def test_text_defs_good_path(cls, info):
    dt = xml_dataclass(cls)
    assert not dt.__children__
    assert not dt.__attributes__
    assert dt.__text_field__ == info


@pytest.mark.parametrize("tp", INVALID_STR_TYPES)
def test_text_defs_bad_path(tp):
    class Foo:
        __ns__ = None
        bar: tp = text()

    with pytest.raises(ValueError) as exc_info:
        xml_dataclass(Foo)

    msg = str(exc_info.value)
    assert "Invalid type" in msg
    assert "'bar'" in msg


@pytest.mark.parametrize(
    "fn,tp,xml_type",
    [
        (child, XmlDt2, XmlFieldType.Child),
        (attr, str, XmlFieldType.Attr),
        (text, str, XmlFieldType.Text),
    ],
)
def test_metadata_passthrough(fn, tp, xml_type):
    cls = make_xml_dt(tp, fn(metadata={"spam": "eggs"}))
    dt = xml_dataclass(cls)
    dt_fields = fields(dt)
    assert len(dt_fields) == 1
    assert dt_fields[0].metadata == {"spam": "eggs", "xml:type": xml_type}


def test_xml_dataclass_no_namespace():
    class Foo:
        bar: str = text()

    with pytest.raises(ValueError) as exc_info:
        xml_dataclass(Foo)

    assert str(exc_info.value) == "XML dataclass without namespace"
    assert exc_info.value.__cause__ is None


def test_xml_dataclass_text_and_children():
    class Foo:
        __ns__ = None
        bar: str = text()
        baz: XmlDt1 = child()

    with pytest.raises(ValueError) as exc_info:
        xml_dataclass(Foo)

    assert (
        str(exc_info.value)
        == "XML dataclass with text-only content has children declared"
    )
    assert exc_info.value.__cause__ is None


def test_xml_dataclass_non_xml_field():
    class Foo:
        __ns__ = None
        bar: str

    with pytest.raises(ValueError) as exc_info:
        xml_dataclass(Foo)

    msg = str(exc_info.value)
    assert "Non-XML field" in msg
    assert "'bar'" in msg
    assert exc_info.value.__cause__ is None


def test_xml_dataclass_unknown_field():
    class Foo:
        __ns__ = None
        bar: str = _xml_field(xml_type=object)

    with pytest.raises(ValueError) as exc_info:
        xml_dataclass(Foo)

    msg = str(exc_info.value)
    assert "Unknown XML field type" in msg
    assert "'object'" in msg


def test_xml_dataclass_child_name_clash():
    class Foo:
        __ns__ = None
        bar: XmlDt2 = child(rename="spam")
        baz: XmlDt2 = child(rename="spam")

    with pytest.raises(ValueError) as exc_info:
        xml_dataclass(Foo)

    msg = str(exc_info.value)
    assert "Duplicate child" in msg
    assert "'spam'" in msg
    assert "'bar'" in msg
    assert "'baz'" in msg


def test_xml_dataclass_attr_name_clash():
    class Foo:
        __ns__ = None
        bar: str = attr(rename="spam")
        baz: str = attr(rename="spam")

    with pytest.raises(ValueError) as exc_info:
        xml_dataclass(Foo)

    msg = str(exc_info.value)
    assert "Duplicate attribute" in msg
    assert "'spam'" in msg
    assert "'bar'" in msg
    assert "'baz'" in msg


def uu(tp, tps, ns, is_opt, is_list):
    return (MockField(tp), (tps, ns, is_opt, is_list))


UNPACKED_UNION_GOOD = [
    uu(XmlDt1, (XmlDt1,), NS, False, False),
    uu(Optional[XmlDt1], (XmlDt1,), NS, True, False),
    uu(XmlDt2, (XmlDt2,), None, False, False),
    uu(Optional[XmlDt2], (XmlDt2,), None, True, False),
    uu(List[XmlDt1], (XmlDt1,), NS, False, True),
    uu(Optional[List[XmlDt1]], (XmlDt1,), NS, True, True),
    uu(Union[XmlDt1, XmlDt3], (XmlDt1, XmlDt3,), NS, False, False),
    uu(Union[XmlDt1, XmlDt3, None], (XmlDt1, XmlDt3,), NS, True, False),
    uu(List[Union[XmlDt1, XmlDt3]], (XmlDt1, XmlDt3,), NS, False, True),
    uu(Optional[List[Union[XmlDt1, XmlDt3]]], (XmlDt1, XmlDt3,), NS, True, True),
]


@pytest.mark.parametrize("f,expected", UNPACKED_UNION_GOOD)
def test__unpack_union_type_good_path(f, expected):
    e_tps, e_ns, e_opt, e_list = expected
    a_tps, a_ns, a_opt, a_list = ChildInfo._unpack_union_type(f)
    assert e_tps == a_tps, "Unpack union type"
    assert e_ns == a_ns, "Unpack union namespace"
    assert e_opt == a_opt, "Unpack union is optional"
    assert e_list == a_list, "Unpack union is list"


@pytest.mark.parametrize(
    "tp", [int, str, object, Dt1, Dt1, List[Optional[XmlDt1]]],
)
def test__unpack_union_type_bad_path(tp):
    f = MockField(tp)
    with pytest.raises(ValueError) as exc_info:
        ChildInfo._unpack_union_type(f)

    msg = str(exc_info.value)
    assert "child must be XML dataclass" in msg
    assert repr(f.type) in msg


def test__unpack_union_type_mismatch_ns():
    f = MockField(Union[XmlDt1, XmlDt2])
    with pytest.raises(ValueError) as exc_info:
        ChildInfo._unpack_union_type(f)

    msg = str(exc_info.value)
    assert NS in msg


def make_ci(tp_in, f, tp_out, xml_name, is_list, is_req, is_opt):
    cls = make_xml_dt(tp_in, f)
    return (cls, ChildInfo(f, "bar", xml_name, (tp_out,), is_list, is_req, is_opt))


@pytest.mark.parametrize(
    "cls,info",
    [
        make_ci(XmlDt1, child(), XmlDt1, f"{{{NS}}}bar", False, True, False),
        make_ci(XmlDt2, child(), XmlDt2, "bar", False, True, False),
        make_ci(
            XmlDt1, child(rename="baz"), XmlDt1, f"{{{NS}}}baz", False, True, False
        ),
        make_ci(XmlDt2, child(rename="baz"), XmlDt2, "baz", False, True, False),
        make_ci(
            Optional[XmlDt2], child(default=None), XmlDt2, "bar", False, False, True
        ),
    ],
)
def test_child_def_good_path(cls, info):
    dt = xml_dataclass(cls)
    assert not dt.__attributes__
    assert not dt.__text_field__
    assert len(dt.__children__) == 1
    bar = dt.__children__[0]
    assert bar == info
