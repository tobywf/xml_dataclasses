from __future__ import annotations

from collections import defaultdict
from typing import Any, Dict, List, Mapping, Optional, Type, TypeVar, Union

from lxml.builder import ElementMaker  # type: ignore[import]
from lxml.etree import _Comment as Comment  # type: ignore[import]

from .lxml_utils import strip_ns
from .options import Options
from .resolve_types import (
    ChildInfo,
    TextInfo,
    XmlDataclass,
    XmlDataclassInstance,
    is_xml_dataclass,
)

_T = TypeVar("_T")


def _load_attributes(
    cls: Type[XmlDataclass], el: Any, options: Options
) -> Mapping[str, str]:
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
                ) from None
            attr_value = attr.get_default()
        processed.add(attr.xml_name)
        values[attr.dt_name] = attr_value

    unprocessed = set(el.attrib.keys()) - processed
    if unprocessed and not options.ignore_unknown_attributes:
        readable = ", ".join(f"'{v}'" for v in unprocessed)
        raise ValueError(f"Found undeclared attributes on '{el.tag}': {readable}")

    return values


def _load_text(info: TextInfo, el: Any) -> Mapping[str, str]:
    child = next(el.iterchildren(), None)
    if child is not None:
        if isinstance(child, Comment):
            raise ValueError(f"Element '{el.tag}' contains comments")
        raise ValueError(f"Element '{el.tag}' has child elements (expected text only)")

    text = el.text
    if text is None:
        if info.is_required:
            raise ValueError(f"Element '{el.tag}' has no text")
        text = info.get_default()

    return {info.dt_name: text}


def _load_children(
    cls: Type[XmlDataclass], el: Any, options: Options
) -> Mapping[str, XmlDataclass]:
    if el.text and el.text.strip():
        raise ValueError(f"Element '{el.tag}' has text (expected child elements only)")

    # child elements can be duplicated
    el_children: Dict[str, List[Any]] = defaultdict(list)
    for e in el.iterchildren():
        if isinstance(e, Comment):
            raise ValueError(f"Element '{el.tag}' contains comments")
        el_children[e.tag].append(e)

    values = {}
    processed = set()

    def _unpack_union_child(
        child: ChildInfo, value: Any
    ) -> Union[XmlDataclass, List[XmlDataclass]]:
        exceptions = []
        # try to find one matching type
        for base_type in child.base_types:
            try:
                return load(base_type, value, options=options)
            except ValueError as e:
                exceptions.append(e)

        raise ValueError(
            f"Invalid child elements found for '{child.dt_name}' in '{el.tag}':\n"
            + "\n".join(str(e) for e in exceptions)
        )

    def _get_one_child_value(child: ChildInfo) -> Any:
        # defaultdict can't raise KeyError
        if child.xml_name in el_children:
            value = el_children[child.xml_name]
        else:
            if not child.is_required:
                return child.get_default()

            raise ValueError(
                f"Required child element '{child.xml_name}' not found in '{el.tag}'"
            )

        if not child.is_list:
            if len(value) != 1:
                raise ValueError(
                    f"Multiple child elements '{child.xml_name}' in '{el.tag}'"
                )
            value = value[0]

        if len(child.base_types) == 1:
            # nice path for default use-case
            base_type = child.base_types[0]
            if child.is_list:
                return [load(base_type, v, options=options) for v in value]
            return load(base_type, value, options=options)

        if child.is_list:
            return [_unpack_union_child(child, v) for v in value]
        return _unpack_union_child(child, value)

    for child in cls.__children__:
        child_value = _get_one_child_value(child)
        processed.add(child.xml_name)
        values[child.dt_name] = child_value

    unprocessed = el_children.keys() - processed
    if unprocessed and not options.ignore_unknown_children:
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


def load(
    cls: Type[XmlDataclassInstance],
    el: Any,
    name: Optional[str] = None,
    options: Optional[Options] = None,
) -> XmlDataclassInstance:
    if not is_xml_dataclass(cls):
        raise ValueError(f"Class '{cls!r}' is not an XML dataclass")

    if not options:
        options = Options()

    if name:
        _validate_name(cls, el, name)

    attr_values = _load_attributes(cls, el, options)
    # are we just looking for text content?
    if cls.__text_field__:
        text_values = _load_text(cls.__text_field__, el)
    else:
        child_values = _load_children(cls, el, options)

    if cls.__text_field__:
        child_values = {}
    else:
        text_values = {}

    instance = cls(**attr_values, **text_values, **child_values)
    instance.__nsmap__ = el.nsmap

    try:
        validate_fn = instance.xml_validate  # type: ignore[attr-defined]
    except AttributeError:
        pass
    else:
        validate_fn()

    return instance


def dump(
    instance: XmlDataclassInstance, name: str, nsmap: Mapping[Optional[str], str]
) -> Any:
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
