from lxml import etree


def lmxl_dump(el):
    encoded = etree.tostring(
        el, encoding="utf-8", pretty_print=True, xml_declaration=True
    )
    return encoded.decode("utf-8")
