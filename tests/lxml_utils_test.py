import pytest

from xml_dataclasses.lxml_utils import format_ns, strip_ns


@pytest.mark.parametrize(
    "name,ns,tag",
    [("foo", None, "foo"), ("foo", "xml", "{xml}foo"), ("foo", "", "foo")],
)
def test_format_ns_good_path(name, ns, tag):
    assert format_ns(name, ns) == tag


@pytest.mark.parametrize(
    "tag,name,ns",
    [("foo", "foo", None), ("{xml}foo", "foo", "xml")],
)
def test_strip_ns_good_path(tag, name, ns):
    assert strip_ns(tag) == (name, ns)


@pytest.mark.parametrize("tag", [None, ""])
def test_strip_ns_bad_path(tag):
    with pytest.raises(ValueError):
        strip_ns(tag)
