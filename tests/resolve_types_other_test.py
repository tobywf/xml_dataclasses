from dataclasses import dataclass, field, fields
from typing import Optional
from unittest.mock import patch

import pytest

from xml_dataclasses.exceptions import (
    XmlDataclassContentsError,
    XmlDataclassDuplicateFieldError,
    XmlDataclassInternalError,
    XmlDataclassModelError,
    XmlDataclassNoNamespaceError,
)
from xml_dataclasses.modifiers import rename, text
from xml_dataclasses.resolve_types import FieldInfo, is_xml_dataclass, xml_dataclass

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


@pytest.mark.parametrize(
    "cls,result",
    [(int, False), (str, False), (object, False), (Dt, False), (XmlDt1, True)],
)
def test_is_xml_dataclass(cls, result):
    assert is_xml_dataclass(cls) is result


def test_xml_dataclass_no_namespace():
    class Foo:
        pass

    with pytest.raises(XmlDataclassNoNamespaceError) as exc_info:
        xml_dataclass(Foo)
    assert exc_info.value.__cause__ is None


def test_xml_dataclass_text_and_children():
    class Foo:
        __ns__ = None
        bar: str = text()
        baz: XmlDt1

    with pytest.raises(XmlDataclassContentsError) as exc_info:
        xml_dataclass(Foo)
    assert exc_info.value.__cause__ is None


def test_xml_dataclass_unknown_field_type():
    class Foo:
        __ns__ = None
        bar: str

    patch_resolve = patch(
        "xml_dataclasses.resolve_types._resolve_field_type",
        autospec=True,
        return_value=FieldInfo(None, "bar", False),
    )
    with pytest.raises(XmlDataclassInternalError) as exc_info:
        with patch_resolve as mock_resolve:
            xml_dataclass(Foo)

    mock_resolve.assert_called_once()
    msg = str(exc_info.value)
    assert "field" in msg
    assert exc_info.value.__cause__ is None


def test_xml_dataclass_nsmap_preserved():
    @xml_dataclass
    class Foo:
        __ns__ = None
        __nsmap__ = {}
        pass

    assert Foo.__nsmap__ is not None


def test_xml_dataclass_child_name_clash():
    class Foo:
        __ns__ = None
        bar: XmlDt2 = rename(name="spam")
        baz: XmlDt2 = rename(name="spam")

    with pytest.raises(XmlDataclassDuplicateFieldError) as exc_info:
        xml_dataclass(Foo)

    msg = str(exc_info.value)
    assert "Duplicate child" in msg
    assert "'spam'" in msg
    assert "'bar'" in msg
    assert "'baz'" in msg
    assert exc_info.value.__cause__ is None


def test_xml_dataclass_attr_name_clash():
    class Foo:
        __ns__ = None
        bar: str = rename(name="spam")
        baz: str = rename(name="spam")

    with pytest.raises(XmlDataclassDuplicateFieldError) as exc_info:
        xml_dataclass(Foo)

    msg = str(exc_info.value)
    assert "Duplicate attribute" in msg
    assert "'spam'" in msg
    assert "'bar'" in msg
    assert "'baz'" in msg
    assert exc_info.value.__cause__ is None


def test_xml_dataclass_text_name_clash():
    class Foo:
        __ns__ = None
        bar: str = text()
        baz: str = text()

    with pytest.raises(XmlDataclassDuplicateFieldError) as exc_info:
        xml_dataclass(Foo)

    msg = str(exc_info.value)
    assert "Duplicate text" in msg
    assert "'bar'" in msg
    assert "'baz'" in msg
    assert exc_info.value.__cause__ is None


def test_xml_dataclass_child_has_namespace():
    class Foo:
        __ns__ = None
        bar: XmlDt2 = rename(ns=NS)

    with pytest.raises(XmlDataclassModelError) as exc_info:
        xml_dataclass(Foo)

    msg = str(exc_info.value)
    assert "namespace" in msg
    assert "'bar'" in msg
    assert exc_info.value.__cause__ is None


def test_xml_dataclass_text_has_namespace():
    class Foo:
        __ns__ = None
        bar: str = rename(text(), ns=NS)

    with pytest.raises(XmlDataclassModelError) as exc_info:
        xml_dataclass(Foo)

    msg = str(exc_info.value)
    assert "namespace" in msg
    assert "'bar'" in msg
    assert exc_info.value.__cause__ is None


def test_xml_dataclass_text_has_rename():
    class Foo:
        __ns__ = None
        bar: str = rename(text(), name="baz")

    with pytest.raises(XmlDataclassModelError) as exc_info:
        xml_dataclass(Foo)

    msg = str(exc_info.value)
    assert "rename" in msg
    assert "'bar'" in msg
    assert exc_info.value.__cause__ is None


@pytest.mark.parametrize(
    "f,is_req",
    [
        (field(), True),
        (field(default=None), False),
        (field(default_factory=lambda: None), False),
    ],
)
def test_field_info_is_required_get_default(f, is_req):
    @xml_dataclass
    class Foo:
        __ns__ = None
        bar: Optional[str] = f

    assert len(Foo.__attributes__) == 1
    attr_info = Foo.__attributes__[0]
    assert attr_info.is_required is is_req

    if is_req:
        with pytest.raises(ValueError) as exc_info:
            attr_info.get_default()
        assert exc_info.value.__cause__ is None
    else:
        assert attr_info.get_default() is None


def test_xml_dataclass_already_a_dataclass_stays_a_dataclass():
    @dataclass
    class Foo:
        __ns__ = None
        bar: str = rename(name="baz")

    Bar = xml_dataclass(Foo)
    dt_fields = fields(Bar)
    assert len(dt_fields) == 1
    assert dt_fields[0].metadata == {"xml:name": "baz"}

    assert len(Bar.__attributes__) == 1
    attr_info = Bar.__attributes__[0]
    assert attr_info.xml_name == "baz"
