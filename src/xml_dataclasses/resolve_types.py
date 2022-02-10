# pylint: disable=unsubscriptable-object
from __future__ import annotations

from dataclasses import MISSING, Field, dataclass, fields, is_dataclass
from typing import _GenericAlias  # type: ignore[attr-defined]
from typing import (
    Any,
    Collection,
    Dict,
    List,
    Mapping,
    Optional,
    Tuple,
    Type,
    TypeVar,
    Union,
    cast,
)

from .exceptions import (
    XmlDataclassContentsError,
    XmlDataclassDuplicateFieldError,
    XmlDataclassInternalError,
    XmlDataclassModelError,
    XmlDataclassNoNamespaceError,
    XmlTypeError,
)
from .lxml_utils import format_ns

NoneType: Type[Any] = type(None)
# Union here is a hack to make this a valid alias
NsMap = Union[Mapping[Optional[str], str]]


class XmlDataclass:
    __ns__: Optional[str]
    __attributes__: Collection[AttrInfo]
    __children__: Collection[ChildInfo]
    __text_field__: Optional[TextInfo]
    __nsmap__: Optional[NsMap]


XmlDataclassInstance = TypeVar("XmlDataclassInstance", bound=XmlDataclass)


def is_xml_dataclass(tp: Type[Any]) -> bool:
    # all XML dataclasses also must be regular dataclasses
    if not is_dataclass(tp):
        return False
    # check required attributes
    try:
        # pylint: disable=pointless-statement
        tp.__ns__
        tp.__attributes__
        tp.__children__
        tp.__text_field__
        tp.__nsmap__
    except AttributeError:
        return False
    return True


@dataclass
class FieldInfo:
    field: Field[Any]
    dt_name: str
    # this is used for dumping
    is_optional: bool

    # this is used for loading
    @property
    def is_required(self) -> bool:
        # https://github.com/python/mypy/issues/6910
        factory = cast(object, self.field.default_factory)
        return self.field.default is MISSING and factory is MISSING

    def get_default(self) -> Any:
        # https://github.com/python/mypy/issues/6910
        factory = cast(object, self.field.default_factory)
        if self.field.default is not MISSING:
            return self.field.default
        if factory is not MISSING:
            default_factory = self.field.default_factory
            return default_factory()
        raise ValueError("Field is required")


@dataclass
class ChildInfo(FieldInfo):
    xml_name: str
    base_types: Tuple[Type[XmlDataclass], ...]
    is_list: bool

    # pylint: disable=too-many-arguments
    @classmethod
    def resolve(
        cls: Type["ChildInfo"],
        f: Field[Any],
        is_optional: bool,
        types: Tuple[Type[XmlDataclass], ...],
        is_list: bool,
        namespace: str,
    ) -> "ChildInfo":
        if "xml:ns" in f.metadata:
            raise XmlDataclassModelError(
                f"Field '{f.name}' is a child and cannot have a namespace"
            )
        rename = f.metadata.get("xml:name")
        xml_name = format_ns(rename if rename else f.name, namespace)

        return cls(f, f.name, is_optional, xml_name, types, is_list)


@dataclass
class AttrInfo(FieldInfo):
    xml_name: str

    @classmethod
    def resolve(cls: Type["AttrInfo"], f: Field[Any], is_optional: bool) -> "AttrInfo":
        rename = f.metadata.get("xml:name")
        namespace = f.metadata.get("xml:ns")
        xml_name = format_ns(rename if rename else f.name, namespace)

        return cls(f, f.name, is_optional, xml_name)


@dataclass
class TextInfo(FieldInfo):
    @classmethod
    def resolve(cls: Type["TextInfo"], f: Field[Any], is_optional: bool) -> "TextInfo":
        if "xml:name" in f.metadata:
            raise XmlDataclassModelError(
                f"Field '{f.name}' is text and cannot be renamed"
            )
        if "xml:ns" in f.metadata:
            raise XmlDataclassModelError(
                f"Field '{f.name}' is text and cannot have a namespace"
            )

        return cls(f, f.name, is_optional)


def _resolve_optional_type(tp: Type[Any]) -> Tuple[Type[Any], bool]:
    # Optional[T] is an alias for Union[T, None], but could also just be Union
    is_union = isinstance(tp, _GenericAlias) and tp.__origin__ is Union
    # not a Union/Optional type, nothing to do
    if not is_union:
        return tp, False

    # figure out if it's an Optional type by removing None
    args_opt = tp.__args__
    args_req = [arg for arg in args_opt if arg is not NoneType]
    is_optional = len(args_opt) > len(args_req)
    if is_optional:
        # typing flattens Optional[Union[T, V]] into Union[T, V]
        if len(args_req) == 1:
            tp = args_req[0]
        else:
            tp = _GenericAlias(Union, tuple(args_req))
        return tp, True
    return tp, False


def _resolve_child_type(
    tp: Type[Any],
) -> Tuple[Tuple[Type[XmlDataclass], ...], bool, str]:
    # next, List/list is allowed, but only at this level (may contain Union)
    is_list = isinstance(tp, _GenericAlias) and tp.__origin__ is list
    if is_list:
        if len(tp.__args__) != 1:
            msg = f"List type has invalid number of arguments ({tp.__args__})"
            raise XmlTypeError(msg)
        tp = tp.__args__[0]
    is_union = isinstance(tp, _GenericAlias) and tp.__origin__ is Union
    if is_union:
        types = tp.__args__
        if any(arg is NoneType for arg in types):
            msg = f"Nested type cannot be optional ({tp!s})"
            raise XmlTypeError(msg)
    else:
        types = [tp]

    for v in types:
        if not is_xml_dataclass(v):
            msg = (
                f"Child type must be XML dataclass ({v!r}). "
                "(If you wanted an attribute, this must be an optional or "
                "required string)"
            )
            raise XmlTypeError(msg)

    namespaces = {v.__ns__ for v in types}
    if len(namespaces) > 1:
        ns_joined = ", ".join(str(ns) for ns in namespaces)
        msg = f"Found different namespaces for child types ({ns_joined})"
        raise XmlTypeError(msg)

    namespace = next(iter(namespaces))

    return tuple(types), is_list, namespace


def _resolve_field_type(f: Field[Any]) -> FieldInfo:
    tp = f.type
    try:
        # do this first, Optional is only allowed at the top-most level
        tp, is_optional = _resolve_optional_type(tp)
        # in future, attributes might be allowed to have other basic types
        if tp is str:
            if f.metadata.get("xml:text") is True:
                return TextInfo.resolve(f, is_optional)
            return AttrInfo.resolve(f, is_optional)
        # should be a child
        types, is_list, namespace = _resolve_child_type(tp)
        return ChildInfo.resolve(f, is_optional, types, is_list, namespace)
    except XmlTypeError as e:
        msg = f"Invalid type '{f.type}' on field '{f.name}'. {e!s}"
        raise XmlTypeError(msg) from e


class _XmlNameTracker:
    def __init__(self, field_type: str):
        self.field_type = field_type
        self.seen: Dict[str, str] = {}

    def add(self, xml_name: str, field_name: str) -> None:
        try:
            previous = self.seen[xml_name]
        except KeyError:
            self.seen[xml_name] = field_name
        else:
            msg = (
                f"Duplicate {self.field_type} '{xml_name}' on '{field_name}', "
                f"previously declared on '{previous}'"
            )
            raise XmlDataclassDuplicateFieldError(msg)


def xml_dataclass(cls: Type[Any]) -> Type[XmlDataclassInstance]:
    # if a dataclass is doubly decorated, metadata seems to disappear...
    if is_dataclass(cls):
        new_cls = cls
    else:
        new_cls = dataclass()(cls)

    try:
        new_cls.__ns__
    except AttributeError:
        raise XmlDataclassNoNamespaceError() from None

    try:
        new_cls.__nsmap__
    except AttributeError:
        new_cls.__nsmap__ = None

    seen_attrs = _XmlNameTracker("attribute")
    seen_children = _XmlNameTracker("child")
    attrs: List[AttrInfo] = []
    children: List[ChildInfo] = []
    text_field = None
    for f in fields(cls):
        # ignore fields not required in the constructor
        if not f.init:
            continue

        field_info = _resolve_field_type(f)
        if isinstance(field_info, TextInfo):
            if text_field is not None:
                msg = (
                    f"Duplicate text field '{field_info.dt_name}', "
                    f"previously declared on '{text_field.dt_name}'"
                )
                raise XmlDataclassDuplicateFieldError(msg)
            text_field = field_info
        elif isinstance(field_info, AttrInfo):
            seen_attrs.add(field_info.xml_name, f.name)
            attrs.append(field_info)
        elif isinstance(field_info, ChildInfo):
            seen_children.add(field_info.xml_name, f.name)
            children.append(field_info)
        else:
            raise XmlDataclassInternalError("Unknown XML field type")

    if text_field and children:
        raise XmlDataclassContentsError()

    new_cls.__attributes__ = attrs
    new_cls.__children__ = children
    new_cls.__text_field__ = text_field

    return new_cls
