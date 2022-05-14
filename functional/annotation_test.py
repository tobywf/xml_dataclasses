from __future__ import annotations

from dataclasses import dataclass

from lxml import etree  # type: ignore[import]

from xml_dataclasses import XmlDataclass, load, xml_dataclass


@xml_dataclass
@dataclass
class Example(XmlDataclass):
    __ns__ = None
    name: str


DOC = """<?xml version="1.0"?><example name="foo" />"""


def test_functional_annotations() -> None:
    parser = etree.XMLParser(remove_blank_text=True)
    el = etree.fromstring(DOC, parser)
    example = load(Example, el, "example")
    assert example.name == "foo"
