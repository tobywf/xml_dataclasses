from dataclasses import dataclass, field
from typing import List, Optional, Union

import pytest
from lxml import etree

# test public exports
from xml_dataclasses import load, text, xml_dataclass

NS = "https://tobywf.com"


@xml_dataclass
class Child1:
    __ns__ = None
    spam: str


@xml_dataclass
class Child2:
    __ns__ = None
    wibble: str


@pytest.mark.parametrize(
    "cls",
    [None, object, str, int, dataclass(type("Foo", (), {}))],
)
def test_load_not_xml_dataclass(cls):
    with pytest.raises(ValueError) as exc_info:
        load(cls, None, "foo")

    assert repr(cls) in str(exc_info.value)


def test_load_validate_name_invalid_name():
    @xml_dataclass
    class Foo:
        __ns__ = None

    el = etree.fromstring("<foo />")
    with pytest.raises(ValueError) as exc_info:
        load(Foo, el, "bar")

    msg = str(exc_info.value)
    assert "'foo'" in msg
    assert "'bar'" in msg


def test_load_validate_name_invalid_ns_one():
    @xml_dataclass
    class Foo:
        __ns__ = NS

    el = etree.fromstring("<foo />")
    with pytest.raises(ValueError) as exc_info:
        load(Foo, el, "foo")

    msg = str(exc_info.value)
    assert el.tag in msg
    assert f"'{NS}'" in msg


def test_load_validate_name_invalid_ns_two():
    @xml_dataclass
    class Foo:
        __ns__ = None

    el = etree.fromstring(f'<foo xmlns="{NS}" />')
    with pytest.raises(ValueError) as exc_info:
        load(Foo, el, "foo")

    msg = str(exc_info.value)
    assert el.tag in msg
    assert f"'{NS}'" in msg


def test_load_attributes_present_required():
    @xml_dataclass
    class Foo:
        __ns__ = None
        bar: str

    el = etree.fromstring('<foo bar="baz" />')
    foo = load(Foo, el, "foo")
    assert foo.bar == "baz"


def test_load_attributes_present_optional():
    @xml_dataclass
    class Foo:
        __ns__ = None
        bar: Optional[str] = None

    el = etree.fromstring('<foo bar="baz" />')
    foo = load(Foo, el, "foo")
    assert foo.bar == "baz"


def test_load_attributes_missing_required():
    @xml_dataclass
    class Foo:
        __ns__ = None
        bar: str

    el = etree.fromstring("<foo />")
    with pytest.raises(ValueError) as exc_info:
        load(Foo, el, "foo")

    msg = str(exc_info.value)
    assert "Required attribute" in msg
    assert "'foo'" in msg
    assert "'bar'" in msg


def test_load_attributes_missing_optional():
    @xml_dataclass
    class Foo:
        __ns__ = None
        bar: Optional[str] = None

    el = etree.fromstring("<foo />")
    foo = load(Foo, el, "foo")
    assert foo.bar is None


def test_load_attributes_missing_default():
    @xml_dataclass
    class Foo:
        __ns__ = None
        bar: str = "baz"

    el = etree.fromstring("<foo />")
    foo = load(Foo, el, "foo")
    assert foo.bar == "baz"


def test_load_attributes_undeclared():
    @xml_dataclass
    class Foo:
        __ns__ = None

    el = etree.fromstring('<foo bar="baz" />')
    with pytest.raises(ValueError) as exc_info:
        load(Foo, el, "foo")

    msg = str(exc_info.value)
    assert "undeclared attributes" in msg
    assert "'foo'" in msg
    assert "'bar'" in msg


def test_load_text_present_required():
    @xml_dataclass
    class Foo:
        __ns__ = None
        value: str = text()

    el = etree.fromstring("<foo>bar</foo>")
    foo = load(Foo, el, "foo")
    assert foo.value == "bar"


def test_load_text_present_optional():
    @xml_dataclass
    class Foo:
        __ns__ = None
        value: Optional[str] = text(default=None)

    el = etree.fromstring("<foo>bar</foo>")
    foo = load(Foo, el, "foo")
    assert foo.value == "bar"


def test_load_text_missing_required():
    @xml_dataclass
    class Foo:
        __ns__ = None
        value: str = text()

    el = etree.fromstring("<foo />")
    with pytest.raises(ValueError) as exc_info:
        load(Foo, el, "foo")

    msg = str(exc_info.value)
    assert "no text" in msg
    assert "'foo'" in msg


def test_load_text_missing_optional():
    @xml_dataclass
    class Foo:
        __ns__ = None
        value: Optional[str] = text(default=None)

    el = etree.fromstring("<foo />")
    foo = load(Foo, el, "foo")
    assert foo.value is None


def test_load_text_missing_default():
    @xml_dataclass
    class Foo:
        __ns__ = None
        value: str = text(default="bar")

    el = etree.fromstring("<foo />")
    foo = load(Foo, el, "foo")
    assert foo.value == "bar"


@pytest.mark.parametrize("xml", ["<foo><bar /></foo>", "<foo>aa<bar />bb</foo>"])
def test_load_text_has_children(xml):
    @xml_dataclass
    class Foo:
        __ns__ = None
        value: str = text()

    el = etree.fromstring(xml)
    with pytest.raises(ValueError) as exc_info:
        load(Foo, el, "foo")

    msg = str(exc_info.value)
    assert "has child elements" in msg
    assert "'foo'" in msg


@pytest.mark.parametrize("xml", ['<foo><bar spam="eggs">baz</bar></foo>'])
def test_load_children_has_text(xml):
    @xml_dataclass
    class Foo:
        __ns__ = None
        bar: Child1

    el = etree.fromstring(xml)
    with pytest.raises(ValueError) as exc_info:
        load(Foo, el, "foo")

    msg = str(exc_info.value)
    assert "has text" in msg
    assert "'bar'" in msg


def test_load_children_single_present_required():
    @xml_dataclass
    class Foo:
        __ns__ = None
        bar: Child1

    el = etree.fromstring('<foo><bar spam="eggs" /></foo>')
    foo = load(Foo, el, "foo")
    assert foo.bar.spam == "eggs"


def test_load_children_single_present_optional():
    @xml_dataclass
    class Foo:
        __ns__ = None
        bar: Optional[Child1] = None

    el = etree.fromstring('<foo><bar spam="eggs" /></foo>')
    foo = load(Foo, el, "foo")
    assert foo.bar.spam == "eggs"


def test_load_children_single_missing_required():
    @xml_dataclass
    class Foo:
        __ns__ = None
        bar: Child1

    el = etree.fromstring("<foo />")
    with pytest.raises(ValueError) as exc_info:
        load(Foo, el, "foo")

    msg = str(exc_info.value)
    assert "Required child element" in msg
    assert "'foo'" in msg
    assert "'bar'" in msg


def test_load_children_single_missing_optional():
    @xml_dataclass
    class Foo:
        __ns__ = None
        bar: Optional[Child1] = None

    el = etree.fromstring("<foo />")
    foo = load(Foo, el, "foo")
    assert foo.bar is None


def test_load_children_single_undeclared():
    @xml_dataclass
    class Foo:
        __ns__ = None

    el = etree.fromstring("<foo><bar /></foo>")
    with pytest.raises(ValueError) as exc_info:
        load(Foo, el, "foo")

    msg = str(exc_info.value)
    assert "undeclared child elements" in msg
    assert "'foo'" in msg
    assert "'bar'" in msg


def test_load_children_single_multiple_els():
    @xml_dataclass
    class Foo:
        __ns__ = None
        bar: Child1

    el = etree.fromstring("<foo><bar /><bar /></foo>")
    with pytest.raises(ValueError) as exc_info:
        load(Foo, el, "foo")

    msg = str(exc_info.value)
    assert "Multiple child elements" in msg
    assert "'foo'" in msg
    assert "'bar'" in msg


def test_load_children_single_missing_default():
    @xml_dataclass
    class Foo:
        __ns__ = None
        bar: Child1 = Child1(spam="eggs")

    el = etree.fromstring("<foo />")
    foo = load(Foo, el, "foo")
    assert foo.bar.spam == "eggs"


def test_load_children_multiple_present_required1():
    @xml_dataclass
    class Foo:
        __ns__ = None
        bar: List[Child1]

    el = etree.fromstring('<foo><bar spam="eggs" /></foo>')
    foo = load(Foo, el, "foo")
    assert len(foo.bar) == 1
    assert foo.bar[0].spam == "eggs"


def test_load_children_multiple_present_required2():
    @xml_dataclass
    class Foo:
        __ns__ = None
        bar: List[Child1]

    el = etree.fromstring('<foo><bar spam="eggs" /><bar spam="ham" /></foo>')
    foo = load(Foo, el, "foo")
    assert len(foo.bar) == 2
    assert foo.bar[0].spam == "eggs"
    assert foo.bar[1].spam == "ham"


def test_load_children_multiple_present_optional():
    @xml_dataclass
    class Foo:
        __ns__ = None
        bar: Optional[List[Child1]] = None

    el = etree.fromstring('<foo><bar spam="eggs" /></foo>')
    foo = load(Foo, el, "foo")
    assert len(foo.bar) == 1
    assert foo.bar[0].spam == "eggs"


def test_load_children_multiple_missing_required():
    @xml_dataclass
    class Foo:
        __ns__ = None
        bar: List[Child1]

    el = etree.fromstring("<foo />")
    with pytest.raises(ValueError) as exc_info:
        load(Foo, el, "foo")

    msg = str(exc_info.value)
    assert "Required child element" in msg
    assert "'foo'" in msg
    assert "'bar'" in msg


def test_load_children_multiple_missing_optional():
    @xml_dataclass
    class Foo:
        __ns__ = None
        bar: Optional[List[Child1]] = None

    el = etree.fromstring("<foo />")
    foo = load(Foo, el, "foo")
    assert foo.bar is None


def test_load_children_multiple_missing_default():
    @xml_dataclass
    class Foo:
        __ns__ = None
        bar: List[Child1] = field(default_factory=lambda: [Child1(spam="eggs")])

    el = etree.fromstring("<foo />")
    foo = load(Foo, el, "foo")
    assert len(foo.bar) == 1
    assert foo.bar[0].spam == "eggs"


def test_load_children_union_present_required1():
    @xml_dataclass
    class Foo:
        __ns__ = None
        bar: Union[Child1, Child2]

    el = etree.fromstring('<foo><bar spam="eggs" /></foo>')
    foo = load(Foo, el, "foo")
    assert isinstance(foo.bar, Child1)
    assert foo.bar.spam == "eggs"


def test_load_children_union_present_required2():
    @xml_dataclass
    class Foo:
        __ns__ = None
        bar: Union[Child1, Child2]

    el = etree.fromstring('<foo><bar wibble="wobble" /></foo>')
    foo = load(Foo, el, "foo")
    assert isinstance(foo.bar, Child2)
    assert foo.bar.wibble == "wobble"


def test_load_children_union_overrepresented():
    @xml_dataclass
    class Foo:
        __ns__ = None
        bar: Union[Child1, Child2]

    el = etree.fromstring('<foo><bar spam="eggs" /><bar wibble="wobble" /></foo>')

    with pytest.raises(ValueError) as exc_info:
        load(Foo, el, "foo")

    msg = str(exc_info.value)
    assert "Multiple child elements" in msg
    assert "'foo'" in msg
    assert "'bar'" in msg


def test_load_children_union_invalid():
    @xml_dataclass
    class Foo:
        __ns__ = None
        bar: Union[Child1, Child2]

    el = etree.fromstring('<foo><bar qux="eggs" /></foo>')

    with pytest.raises(ValueError) as exc_info:
        load(Foo, el, "foo")

    msg = str(exc_info.value)
    assert "Invalid child elements" in msg
    assert "'foo'" in msg
    assert "'bar'" in msg


def test_load_children_union_multiple():
    @xml_dataclass
    class Foo:
        __ns__ = None
        bar: List[Union[Child1, Child2]]

    el = etree.fromstring('<foo><bar spam="eggs" /><bar wibble="wobble" /></foo>')

    foo = load(Foo, el, "foo")
    assert len(foo.bar) == 2
    assert isinstance(foo.bar[0], Child1)
    assert foo.bar[0].spam == "eggs"
    assert isinstance(foo.bar[1], Child2)
    assert foo.bar[1].wibble == "wobble"


def test_load_children_union_present_optional():
    @xml_dataclass
    class Foo:
        __ns__ = None
        bar: Optional[Union[Child1, Child2]] = None

    el = etree.fromstring('<foo><bar spam="eggs" /></foo>')
    foo = load(Foo, el, "foo")
    assert isinstance(foo.bar, Child1)
    assert foo.bar.spam == "eggs"


def test_load_children_union_missing_required():
    @xml_dataclass
    class Foo:
        __ns__ = None
        bar: Union[Child1, Child2]

    el = etree.fromstring("<foo />")
    with pytest.raises(ValueError) as exc_info:
        load(Foo, el, "foo")

    msg = str(exc_info.value)
    assert "Required child element" in msg
    assert "'foo'" in msg
    assert "'bar'" in msg


def test_load_children_union_missing_optional():
    @xml_dataclass
    class Foo:
        __ns__ = None
        bar: Optional[Union[Child1, Child2]] = None

    el = etree.fromstring("<foo />")
    foo = load(Foo, el, "foo")
    assert foo.bar is None


def test_load_children_union_missing_default():
    @xml_dataclass
    class Foo:
        __ns__ = None
        bar: Union[Child1, Child2] = Child1(spam="eggs")

    el = etree.fromstring("<foo />")
    foo = load(Foo, el, "foo")
    assert isinstance(foo.bar, Child1)
    assert foo.bar.spam == "eggs"


def test_load_with_validation():
    class MyError(Exception):
        pass

    @xml_dataclass
    class Foo:
        __ns__ = None
        bar: str

        def xml_validate(self) -> None:
            if self.bar == "baz":
                raise MyError()

    el = etree.fromstring('<foo bar="baz" />')
    with pytest.raises(MyError):
        load(Foo, el, "foo")
