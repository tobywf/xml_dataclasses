from pathlib import Path
from typing import List

from lxml import etree

from xml_dataclasses import attr, child, dump, load, xml_dataclass

BASE = Path(__file__).resolve(strict=True).parent

CONTAINER_NS = "urn:oasis:names:tc:opendocument:xmlns:container"


@xml_dataclass
class RootFile:
    __ns__ = CONTAINER_NS
    full_path: str = attr(rename="full-path")
    media_type: str = attr(rename="media-type")


@xml_dataclass
class RootFiles:
    __ns__ = CONTAINER_NS
    rootfile: List[RootFile] = child()


@xml_dataclass
class Container:
    __ns__ = CONTAINER_NS
    version: str = attr()
    rootfiles: RootFiles = child()
    # WARNING: this is an incomplete implementation of an OPF container
    # (it's missing links)


def lmxl_dump(el):
    encoded = etree.tostring(
        el, encoding="utf-8", pretty_print=True, xml_declaration=True
    )
    return encoded.decode("utf-8")


def test_functional_container():
    el = etree.parse(str(BASE / "container.xml")).getroot()
    original = lmxl_dump(el)
    container = load(Container, el, "container")
    assert container == Container(
        version="1.0",
        rootfiles=RootFiles(
            rootfile=[
                RootFile(
                    full_path="OEBPS/content.opf",
                    media_type="application/oebps-package+xml",
                ),
            ],
        ),
    )
    el = dump(container, "container", {None: CONTAINER_NS})
    roundtrip = lmxl_dump(el)
    assert original == roundtrip
