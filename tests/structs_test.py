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
    _unpack_union_type,
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


@pytest.mark.parametrize(
    "cls,result", [(object, False), (Dt1, False), (XmlDt1, True)],
)
def test_is_xml_dataclass(cls, result):
    assert is_xml_dataclass(cls) is result


@pytest.mark.parametrize(
    "type_in,type_out",
    [
        (str, str),
        (Optional[str], str),
        (Optional[List[str]], List[str]),
        (XmlDataclass, XmlDataclass),
        (Optional[XmlDataclass], XmlDataclass),
        (Optional[List[XmlDataclass]], List[XmlDataclass]),
    ],
)
def test__unpack_union_type_good_path(type_in, type_out):
    f = MockField(tp=type_in)
    assert _unpack_union_type(f) is type_out


@pytest.mark.parametrize("type_in", [Union[str, XmlDataclass]])
def test__unpack_union_type_bad_path(type_in):
    f = MockField(tp=type_in)

    with pytest.raises(ValueError):
        _unpack_union_type(f)


def make_ci(tp_in, f, tp_out, xml_name, is_list, is_req, is_opt):
    cls = make_xml_dt(tp_in, f)
    return (cls, ChildInfo(f, "bar", xml_name, tp_out, is_list, is_req, is_opt))


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
            Optional[XmlDt1],
            child(default=None),
            XmlDt1,
            f"{{{NS}}}bar",
            False,
            False,
            True,
        ),
        make_ci(
            Optional[XmlDt2], child(default=None), XmlDt2, "bar", False, False, True
        ),
        make_ci(List[XmlDt1], child(), XmlDt1, f"{{{NS}}}bar", True, True, False),
        make_ci(List[XmlDt2], child(), XmlDt2, "bar", True, True, False),
        make_ci(
            Optional[List[XmlDt1]],
            child(default=None),
            XmlDt1,
            f"{{{NS}}}bar",
            True,
            False,
            True,
        ),
        make_ci(
            Optional[List[XmlDt2]],
            child(default=None),
            XmlDt2,
            "bar",
            True,
            False,
            True,
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


@pytest.mark.parametrize("tp", [Dt1, str, Optional[str], List[str], int, Optional[int]])
def test_child_def_bad_path(tp):
    class Foo:
        __ns__ = None
        bar: tp = child()

    with pytest.raises(ValueError) as exc_info:
        xml_dataclass(Foo)

    msg = str(exc_info.value)
    assert "Invalid type" in msg
    assert "'bar'" in msg


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


@pytest.mark.parametrize("tp", [int, Optional[int], Dt1, XmlDt1, List[XmlDt1]])
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


@pytest.mark.parametrize("tp", [int, Optional[int], Dt1, XmlDt1, List[XmlDt1]])
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
