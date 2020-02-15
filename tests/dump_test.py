from dataclasses import dataclass
from typing import List, Optional

import pytest
from lxml import etree

# test public exports
from xml_dataclasses import attr, child, dump, text, xml_dataclass

NS = "https://tobywf.com"
NSMAP = {None: NS}


@xml_dataclass
class Child:
    __ns__ = None


@pytest.mark.parametrize(
    "inst", [None, object(), "", 0, dataclass(type("Foo", (), {}))],
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
        bar: str = attr()

    foo = Foo(bar="baz")
    el = dump(foo, "foo", None)
    xml = etree.tounicode(el)
    assert xml == '<foo bar="baz"/>'


def test_dump_attributes_present_optional():
    @xml_dataclass
    class Foo:
        __ns__ = None
        bar: Optional[str] = attr(default=None)

    foo = Foo(bar="baz")
    el = dump(foo, "foo", None)
    xml = etree.tounicode(el)
    assert xml == '<foo bar="baz"/>'


def test_dump_attributes_missing_optional():
    @xml_dataclass
    class Foo:
        __ns__ = None
        bar: Optional[str] = attr(default=None)

    foo = Foo()
    el = dump(foo, "foo", None)
    xml = etree.tounicode(el)
    assert xml == "<foo/>"


def test_dump_attributes_missing_default():
    @xml_dataclass
    class Foo:
        __ns__ = None
        bar: str = attr(default="baz")

    foo = Foo()
    el = dump(foo, "foo", None)
    xml = etree.tounicode(el)
    assert xml == '<foo bar="baz"/>'


def test_dump_text_present_required():
    @xml_dataclass
    class Foo:
        __ns__ = None
        value: str = text()

    foo = Foo(value="bar")
    el = dump(foo, "foo", None)
    xml = etree.tounicode(el)
    assert xml == "<foo>bar</foo>"


def test_dump_text_present_optional():
    @xml_dataclass
    class Foo:
        __ns__ = None
        value: Optional[str] = text(default=None)

    foo = Foo(value="bar")
    el = dump(foo, "foo", None)
    xml = etree.tounicode(el)
    assert xml == "<foo>bar</foo>"


def test_dump_text_missing_optional():
    @xml_dataclass
    class Foo:
        __ns__ = None
        value: Optional[str] = text(default=None)

    foo = Foo()
    el = dump(foo, "foo", None)
    xml = etree.tounicode(el)
    assert xml == "<foo/>"


def test_dump_text_missing_default():
    @xml_dataclass
    class Foo:
        __ns__ = None
        value: str = text(default="bar")

    foo = Foo()
    el = dump(foo, "foo", None)
    xml = etree.tounicode(el)
    assert xml == "<foo>bar</foo>"


def test_dump_children_single_present_required():
    @xml_dataclass
    class Foo:
        __ns__ = None
        bar: Child = child()

    foo = Foo(bar=Child())
    el = dump(foo, "foo", None)
    xml = etree.tounicode(el)
    assert xml == "<foo><bar/></foo>"


def test_dump_children_single_present_optional():
    @xml_dataclass
    class Foo:
        __ns__ = None
        bar: Optional[Child] = child(default=None)

    foo = Foo(bar=Child())
    el = dump(foo, "foo", None)
    xml = etree.tounicode(el)
    assert xml == "<foo><bar/></foo>"


def test_dump_children_single_missing_optional():
    @xml_dataclass
    class Foo:
        __ns__ = None
        bar: Optional[Child] = child(default=None)

    foo = Foo()
    el = dump(foo, "foo", None)
    xml = etree.tounicode(el)
    assert xml == "<foo/>"


def test_dump_children_single_missing_default():
    @xml_dataclass
    class Foo:
        __ns__ = None
        bar: Child = child(default=Child())

    foo = Foo()
    el = dump(foo, "foo", None)
    xml = etree.tounicode(el)
    assert xml == "<foo><bar/></foo>"


def test_dump_children_multiple_present_required1():
    @xml_dataclass
    class Foo:
        __ns__ = None
        bar: List[Child] = child()

    foo = Foo(bar=[Child()])
    el = dump(foo, "foo", None)
    xml = etree.tounicode(el)
    assert xml == "<foo><bar/></foo>"


def test_dump_children_multiple_present_required2():
    @xml_dataclass
    class Foo:
        __ns__ = None
        bar: List[Child] = child()

    foo = Foo(bar=[Child(), Child()])
    el = dump(foo, "foo", None)
    xml = etree.tounicode(el)
    assert xml == "<foo><bar/><bar/></foo>"


def test_dump_children_multiple_present_optional():
    @xml_dataclass
    class Foo:
        __ns__ = None
        bar: Optional[List[Child]] = child(default=None)

    foo = Foo(bar=[Child(), Child()])
    el = dump(foo, "foo", None)
    xml = etree.tounicode(el)
    assert xml == "<foo><bar/><bar/></foo>"


def test_dump_children_multiple_missing_optional():
    @xml_dataclass
    class Foo:
        __ns__ = None
        bar: Optional[List[Child]] = child(default=None)

    foo = Foo()
    el = dump(foo, "foo", None)
    xml = etree.tounicode(el)
    assert xml == "<foo/>"


def test_dump_children_multiple_missing_default():
    # Can't do this without default_factory
    # @xml_dataclass
    # class Foo:
    #     __ns__ = None
    #     bar: List[Child] = child(default=[Child(), Child()])

    # foo = Foo()
    # el = dump(foo, "foo", None)
    # xml = etree.tounicode(el)
    # assert xml == "<foo><bar/><bar/></foo>"
    pass
