from dataclasses import dataclass, field
from typing import List, Optional, Union

import pytest
from lxml import etree

# test public exports
from xml_dataclasses import dump, text, xml_dataclass

NS = "https://tobywf.com"
NSMAP = {None: NS}


@xml_dataclass
class Child:
    __ns__ = None


@xml_dataclass
class Child1:
    __ns__ = None
    spam: str


@xml_dataclass
class Child2:
    __ns__ = None
    wibble: str


@pytest.mark.parametrize(
    "inst",
    [None, object(), "", 0, dataclass(type("Foo", (), {}))],
)
def test_dump_not_xml_dataclass(inst):
    with pytest.raises(ValueError) as exc_info:
        dump(inst, "foo", NSMAP)

    assert repr(type(inst)) in str(exc_info.value)


def test_dump_resolve_nsmap_passed():
    @xml_dataclass
    class Foo:
        __ns__ = None
        __nsmap__ = None

    foo = Foo()
    el = dump(foo, "foo", NSMAP)
    assert el.nsmap == NSMAP


def test_dump_resolve_nsmap_implicit():
    @xml_dataclass
    class Foo:
        __ns__ = None
        __nsmap__ = NSMAP

    foo = Foo()
    el = dump(foo, "foo", None)
    assert el.nsmap == NSMAP


def test_dump_attributes_present_required():
    @xml_dataclass
    class Foo:
        __ns__ = None
        bar: str

    foo = Foo(bar="baz")
    el = dump(foo, "foo", None)
    xml = etree.tostring(el, encoding="unicode")
    assert xml == '<foo bar="baz"/>'


def test_dump_attributes_present_optional():
    @xml_dataclass
    class Foo:
        __ns__ = None
        bar: Optional[str] = None

    foo = Foo(bar="baz")
    el = dump(foo, "foo", None)
    xml = etree.tostring(el, encoding="unicode")
    assert xml == '<foo bar="baz"/>'


def test_dump_attributes_missing_optional():
    @xml_dataclass
    class Foo:
        __ns__ = None
        bar: Optional[str] = None

    foo = Foo()
    el = dump(foo, "foo", None)
    xml = etree.tostring(el, encoding="unicode")
    assert xml == "<foo/>"


def test_dump_attributes_missing_default():
    @xml_dataclass
    class Foo:
        __ns__ = None
        bar: str = field(default="baz")

    foo = Foo()
    el = dump(foo, "foo", None)
    xml = etree.tostring(el, encoding="unicode")
    assert xml == '<foo bar="baz"/>'


def test_dump_text_present_required():
    @xml_dataclass
    class Foo:
        __ns__ = None
        value: str = text()

    foo = Foo(value="bar")
    el = dump(foo, "foo", None)
    xml = etree.tostring(el, encoding="unicode")
    assert xml == "<foo>bar</foo>"


def test_dump_text_present_optional():
    @xml_dataclass
    class Foo:
        __ns__ = None
        value: Optional[str] = text(default=None)

    foo = Foo(value="bar")
    el = dump(foo, "foo", None)
    xml = etree.tostring(el, encoding="unicode")
    assert xml == "<foo>bar</foo>"


def test_dump_text_missing_optional():
    @xml_dataclass
    class Foo:
        __ns__ = None
        value: Optional[str] = text(default=None)

    foo = Foo()
    el = dump(foo, "foo", None)
    xml = etree.tostring(el, encoding="unicode")
    assert xml == "<foo/>"


def test_dump_text_missing_default():
    @xml_dataclass
    class Foo:
        __ns__ = None
        value: str = text(default="bar")

    foo = Foo()
    el = dump(foo, "foo", None)
    xml = etree.tostring(el, encoding="unicode")
    assert xml == "<foo>bar</foo>"


def test_dump_children_single_present_required():
    @xml_dataclass
    class Foo:
        __ns__ = None
        bar: Child

    foo = Foo(bar=Child())
    el = dump(foo, "foo", None)
    xml = etree.tostring(el, encoding="unicode")
    assert xml == "<foo><bar/></foo>"


def test_dump_children_single_present_optional():
    @xml_dataclass
    class Foo:
        __ns__ = None
        bar: Optional[Child] = None

    foo = Foo(bar=Child())
    el = dump(foo, "foo", None)
    xml = etree.tostring(el, encoding="unicode")
    assert xml == "<foo><bar/></foo>"


def test_dump_children_single_missing_optional():
    @xml_dataclass
    class Foo:
        __ns__ = None
        bar: Optional[Child] = None

    foo = Foo()
    el = dump(foo, "foo", None)
    xml = etree.tostring(el, encoding="unicode")
    assert xml == "<foo/>"


def test_dump_children_single_missing_default():
    @xml_dataclass
    class Foo:
        __ns__ = None
        bar: Child = Child()

    foo = Foo()
    el = dump(foo, "foo", None)
    xml = etree.tostring(el, encoding="unicode")
    assert xml == "<foo><bar/></foo>"


def test_dump_children_multiple_present_required1():
    @xml_dataclass
    class Foo:
        __ns__ = None
        bar: List[Child]

    foo = Foo(bar=[Child()])
    el = dump(foo, "foo", None)
    xml = etree.tostring(el, encoding="unicode")
    assert xml == "<foo><bar/></foo>"


def test_dump_children_multiple_present_required2():
    @xml_dataclass
    class Foo:
        __ns__ = None
        bar: List[Child]

    foo = Foo(bar=[Child(), Child()])
    el = dump(foo, "foo", None)
    xml = etree.tostring(el, encoding="unicode")
    assert xml == "<foo><bar/><bar/></foo>"


def test_dump_children_multiple_present_optional():
    @xml_dataclass
    class Foo:
        __ns__ = None
        bar: Optional[List[Child]] = None

    foo = Foo(bar=[Child(), Child()])
    el = dump(foo, "foo", None)
    xml = etree.tostring(el, encoding="unicode")
    assert xml == "<foo><bar/><bar/></foo>"


def test_dump_children_multiple_missing_optional():
    @xml_dataclass
    class Foo:
        __ns__ = None
        bar: Optional[List[Child]] = None

    foo = Foo()
    el = dump(foo, "foo", None)
    xml = etree.tostring(el, encoding="unicode")
    assert xml == "<foo/>"


def test_dump_children_multiple_missing_default():
    @xml_dataclass
    class Foo:
        __ns__ = None
        bar: List[Child] = field(default_factory=lambda: [Child(), Child()])

    foo = Foo()
    el = dump(foo, "foo", None)
    xml = etree.tostring(el, encoding="unicode")
    assert xml == "<foo><bar/><bar/></foo>"


def test_dump_children_union_present_required1():
    @xml_dataclass
    class Foo:
        __ns__ = None
        bar: Union[Child1, Child2]

    foo = Foo(bar=Child1(spam="eggs"))
    el = dump(foo, "foo", None)
    xml = etree.tostring(el, encoding="unicode")
    assert xml == '<foo><bar spam="eggs"/></foo>'


def test_dump_children_union_present_required2():
    @xml_dataclass
    class Foo:
        __ns__ = None
        bar: Union[Child1, Child2]

    foo = Foo(bar=Child2(wibble="wobble"))
    el = dump(foo, "foo", None)
    xml = etree.tostring(el, encoding="unicode")
    assert xml == '<foo><bar wibble="wobble"/></foo>'


UNION_OPTIONAL = [
    Optional[Union[Child1, Child2]],
    Union[Child1, Child2, None],
]


@pytest.mark.parametrize("tp", UNION_OPTIONAL)
def test_dump_children_union_present_optional(tp):
    @xml_dataclass
    class Foo:
        __ns__ = None
        bar: tp = None

    foo = Foo(bar=Child1(spam="eggs"))
    el = dump(foo, "foo", None)
    xml = etree.tostring(el, encoding="unicode")
    assert xml == '<foo><bar spam="eggs"/></foo>'


@pytest.mark.parametrize("tp", UNION_OPTIONAL)
def test_dump_children_union_missing_optional(tp):
    @xml_dataclass
    class Foo:
        __ns__ = None
        bar: tp = None

    foo = Foo()
    el = dump(foo, "foo", None)
    xml = etree.tostring(el, encoding="unicode")
    assert xml == "<foo/>"


def test_dump_children_union_missing_default():
    @xml_dataclass
    class Foo:
        __ns__ = None
        bar: Union[Child1, Child2] = Child1(spam="eggs")

    foo = Foo()
    el = dump(foo, "foo", None)
    xml = etree.tostring(el, encoding="unicode")
    assert xml == '<foo><bar spam="eggs"/></foo>'


def test_dump_children_union_multiple():
    @xml_dataclass
    class Foo:
        __ns__ = None
        bar: List[Union[Child1, Child2]]

    foo = Foo(bar=[Child1(spam="eggs"), Child2(wibble="wobble")])
    el = dump(foo, "foo", None)
    xml = etree.tostring(el, encoding="unicode")
    assert xml == '<foo><bar spam="eggs"/><bar wibble="wobble"/></foo>'
