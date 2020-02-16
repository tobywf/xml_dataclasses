from enum import Enum
from pathlib import Path
from typing import List, Mapping, Optional, Union

from lxml import etree

from xml_dataclasses import dump, load, rename, text, xml_dataclass

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
    id: Optional[str] = None


@xml_dataclass
class MdMeta3:
    __ns__ = NsMap.opf.value

    property: str
    value: str = text()


@xml_dataclass
class MdMeta2:
    __ns__ = NsMap.opf.value
    content: str
    name: str


@xml_dataclass
class Metadata3:
    __ns__ = NsMap.opf.value

    identifier: List[DublinCoreMd]
    title: List[DublinCoreMd]
    language: List[DublinCoreMd]
    meta: List[Union[MdMeta3, MdMeta2]]


@xml_dataclass
class Item3:
    __ns__ = NsMap.opf.value
    id: str
    href: str
    media_type: str = rename(name="media-type")


@xml_dataclass
class Manifest3:
    __ns__ = NsMap.opf.value
    item: List[Item3]


@xml_dataclass
class ItemRef3:
    __ns__ = NsMap.opf.value
    idref: str
    properties: Optional[str] = None


@xml_dataclass
class Spine3:
    __ns__ = NsMap.opf.value
    itemref: List[ItemRef3]
    toc: Optional[str] = None


@xml_dataclass
class Package3:
    __ns__ = NsMap.opf.value
    version: str
    unique_identifier: str = rename(name="unique-identifier")
    metadata: Metadata3
    manifest: Manifest3
    spine: Spine3
    id: Optional[str] = None
    lang: Optional[str] = rename(default=None, ns=NsMap.xml.value)
    dir: Optional[str] = None


def test_functional_package():
    parser = etree.XMLParser(remove_blank_text=True)
    el = etree.parse(str(BASE / "package.xml"), parser).getroot()
    original = lmxl_dump(el)
    package = load(Package3, el, "package")
    el = dump(package, "package", NsMap.to_dict(NsMap.opf.value))
    roundtrip = lmxl_dump(el)
    assert original == roundtrip
