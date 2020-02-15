from __future__ import annotations

from collections import defaultdict
from typing import Any, Dict, List, Mapping, Optional, Type, TypeVar

from lxml.builder import ElementMaker  # type: ignore

from .lxml_utils import strip_ns
from .structs import ChildInfo, TextInfo, XmlDataclass, is_xml_dataclass

_T = TypeVar("_T")


def _unpack_child(info: ChildInfo[_T], value: Any, el_tag: str) -> Any:
    if info.is_list:
        return [load(info.base_type, v) for v in value]

    if len(value) != 1:
        raise ValueError(f"Multiple child elements '{info.xml_name}' in '{el_tag}'")

    return load(info.base_type, value[0])


def _load_attributes(cls: Type[XmlDataclass], el: Any) -> Mapping[str, str]:
    values = {}
    processed = set()

    # can't have multiple attributes with the same name, so this is easier
    for attr in cls.__attributes__:
        # attributes are strings for now
        try:
            attr_value = el.attrib[attr.xml_name]
        except KeyError:
            if attr.is_required:
                raise ValueError(
                    f"Required attribute '{attr.xml_name}' not found on '{el.tag}'"
                )
            attr_value = attr.field.default
        processed.add(attr.xml_name)
        values[attr.dt_name] = attr_value

    unprocessed = set(el.attrib.keys()) - processed
    if unprocessed:
        readable = ", ".join(f"'{v}'" for v in unprocessed)
        raise ValueError(f"Found undeclared attributes on '{el.tag}': {readable}")

    return values


def _load_text(info: TextInfo[Any], el: Any) -> Mapping[str, str]:
    has_child = next(el.iterchildren(), None) is not None
    if has_child:
        raise ValueError(f"Element '{el.tag}' has child elements (expected text only)")

    text = el.text
    if text is None:
        if info.is_required:
            raise ValueError(f"Element '{el.tag}' has no text")
        text = info.field.default

    return {info.dt_name: text}


def _load_children(cls: Type[XmlDataclass], el: Any) -> Mapping[str, XmlDataclass]:
    # child elements can be duplicated
    el_children: Dict[str, List[Any]] = defaultdict(list)
    for e in el.iterchildren():
        el_children[e.tag].append(e)

    values = {}
    processed = set()

    for child in cls.__children__:
        # defaultdict can't raise KeyError
        if child.xml_name in el_children:
            child_value = _unpack_child(child, el_children[child.xml_name], el.tag)
        else:
            if child.is_required:
                raise ValueError(
                    f"Required child element '{child.xml_name}' not found in '{el.tag}'"
                )
            child_value = child.field.default
        processed.add(child.xml_name)
        values[child.dt_name] = child_value

    unprocessed = el_children.keys() - processed
    if unprocessed:
        readable = ", ".join(f"'{v}'" for v in unprocessed)
        raise ValueError(f"Found undeclared child elements on '{el.tag}': {readable}")

    return values


def _validate_name(cls: Type[XmlDataclass], el: Any, name: str) -> None:
    el_name, el_ns = strip_ns(el.tag)
    if el_name != name:
        raise ValueError(f"Found element '{el_name}', expected '{name}' ('{el.tag}')")
    if el_ns != cls.__ns__:
        raise ValueError(
            f"Found namespace '{el_ns}', expected '{cls.__ns__}' ('{el.tag}')"
        )


def load(cls: Type[XmlDataclass], el: Any, name: Optional[str] = None) -> XmlDataclass:
    if not is_xml_dataclass(cls):
        raise ValueError(f"Class '{cls!r}' is not an XML dataclass")

    if name:
        _validate_name(cls, el, name)

    attr_values = _load_attributes(cls, el)
    # are we just looking for text content?
    if cls.__text_field__:
        text_values = _load_text(cls.__text_field__, el)
    else:
        child_values = _load_children(cls, el)

    if cls.__text_field__:
        child_values = {}
    else:
        text_values = {}

    instance = cls(**attr_values, **text_values, **child_values)  # type: ignore
    instance.__nsmap__ = el.nsmap
    return instance


def dump(instance: XmlDataclass, name: str, nsmap: Mapping[Optional[str], str]) -> Any:
    cls = type(instance)
    if not is_xml_dataclass(cls):
        raise ValueError(f"Class '{cls!r}' is not an XML dataclass")

    resolved_nsmap = instance.__nsmap__ if instance.__nsmap__ else nsmap
    maker = ElementMaker(namespace=instance.__ns__, nsmap=resolved_nsmap)
    el = maker(name)

    for attr in instance.__attributes__:
        attr_value: Any = getattr(instance, attr.dt_name)
        if not (attr.is_optional and attr_value is None):
            el.attrib[attr.xml_name] = attr_value

    text = instance.__text_field__
    if text:
        text_value: Any = getattr(instance, text.dt_name)
        el.text = text_value
    else:
        for child in instance.__children__:
            child_value: Any = getattr(instance, child.dt_name)
            if child.is_optional and child_value is None:
                continue
            if child.is_list:
                for value in child_value:
                    el.append(dump(value, child.xml_name, nsmap))
            else:
                el.append(dump(child_value, child.xml_name, nsmap))

    return el
