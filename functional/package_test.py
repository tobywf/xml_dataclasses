from enum import Enum
from pathlib import Path
from typing import List, Mapping, Optional, Union

from lxml import etree

from xml_dataclasses import attr, child, dump, load, text, xml_dataclass

from .utils import lmxl_dump

BASE = Path(__file__).resolve(strict=True).parent


class NsMap(Enum):
    xml = "http://www.w3.org/XML/1998/namespace"
    opf = "http://www.idpf.org/2007/opf"
    dc = "http://purl.org/dc/elements/1.1/"
    dcterms = "http://purl.org/dc/terms/"

    @classmethod
    def to_dict(cls, default_ns: Optional[str] = None) -> Mapping[Optional[str], str]:
        nsmap = dict(cls.__members__)
        if default_ns:
            nsmap[None] = default_ns
        return nsmap


@xml_dataclass
class DublinCoreMd:
    __ns__ = NsMap.dc.value
    value: str = text()
    id: Optional[str] = attr(default=None)


@xml_dataclass
class MdMeta3:
    __ns__ = NsMap.opf.value

    property: str = attr()
    value: str = text()


@xml_dataclass
class MdMeta2:
    __ns__ = NsMap.opf.value
    content: str = attr()
    name: str = attr()


@xml_dataclass
class Metadata3:
    __ns__ = NsMap.opf.value

    identifier: List[DublinCoreMd] = child()
    title: List[DublinCoreMd] = child()
    language: List[DublinCoreMd] = child()
    meta: List[Union[MdMeta3, MdMeta2]] = child()


@xml_dataclass
class Item3:
    __ns__ = NsMap.opf.value
    id: str = attr()
    href: str = attr()
    media_type: str = attr(rename="media-type")


@xml_dataclass
class Manifest3:
    __ns__ = NsMap.opf.value
    item: List[Item3] = child()


@xml_dataclass
class ItemRef3:
    __ns__ = NsMap.opf.value
    idref: str = attr()
    properties: Optional[str] = attr(default=None)


@xml_dataclass
class Spine3:
    __ns__ = NsMap.opf.value
    itemref: List[ItemRef3] = child()
    toc: Optional[str] = attr(default=None)


@xml_dataclass
class Package3:
    __ns__ = NsMap.opf.value
    version: str = attr()
    unique_identifier: str = attr(rename="unique-identifier")
    metadata: Metadata3 = child()
    manifest: Manifest3 = child()
    spine: Spine3 = child()
    id: Optional[str] = attr(default=None)
    lang: Optional[str] = attr(default=None, namespace=NsMap.xml.value)
    dir: Optional[str] = attr(default=None)


def test_functional_package():
    parser = etree.XMLParser(remove_blank_text=True)
    el = etree.parse(str(BASE / "package.xml"), parser).getroot()
    original = lmxl_dump(el)
    package = load(Package3, el, "package")
    el = dump(package, "package", NsMap.to_dict(NsMap.opf.value))
    roundtrip = lmxl_dump(el)
    assert original == roundtrip
