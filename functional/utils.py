from typing import Any

from lxml import etree  # type: ignore


def lmxl_dump(el: Any) -> str:
    encoded: bytes = etree.tostring(
        el, encoding="utf-8", pretty_print=True, xml_declaration=True
    )
    return encoded.decode("utf-8")
