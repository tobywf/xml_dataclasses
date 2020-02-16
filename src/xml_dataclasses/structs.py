# pylint: disable=unsubscriptable-object
# unsubscriptable-object clashes with type hints
from __future__ import annotations

from dataclasses import (
    _MISSING_TYPE,
    MISSING,
    Field,
    dataclass,
    field,
    fields,
    is_dataclass,
)
from enum import Enum, auto
from typing import (
    Any,
    Collection,
    Dict,
    Generic,
    List,
    Mapping,
    Optional,
    Tuple,
    Type,
    TypeVar,
    Union,
    cast,
)

from typing_inspect import get_args, get_origin, is_union_type  # type: ignore

from .lxml_utils import format_ns

_T = TypeVar("_T")
NoneType: Type[Any] = type(None)


class XmlFieldType(Enum):
    Attr = auto()
    Child = auto()
    Text = auto()


def is_xml_dataclass(tp: Type[Any]) -> bool:
    # all XML dataclasses also must be regular dataclasses
    if not is_dataclass(tp):
        return False
    # pylint: disable=pointless-statement
    # check required attributes
    try:
        tp.__ns__
        tp.__attributes__
        tp.__children__
        tp.__nsmap__
    except AttributeError:
        return False
    return True


def _is_required(f: Field[_T]) -> bool:
    return f.default is MISSING


def _check_str_type(f: Field[_T]) -> bool:
    tp = f.type
    if is_union_type(tp):
        # this basically resolves Optional types by removing None
        args_old: List[Type[Any]] = get_args(f.type)
        args_new = [arg for arg in args_old if arg is not NoneType]
        if len(args_new) != 1:
            raise ValueError(f"Invalid type '{f.type}' on field '{f.name}' (union?)")
        tp = args_new[0]
        is_optional = len(args_old) > len(args_new)
    else:
        is_optional = False

    if tp is not str:
        msg = (
            f"Invalid type '{f.type}' on field '{f.name}' " "(attribute must be 'str')"
        )
        raise ValueError(msg)

    return is_optional


@dataclass
class ChildInfo(Generic[_T]):
    field: Field[_T]
    dt_name: str
    xml_name: str
    base_types: Tuple[Type[XmlDataclass]]
    is_list: bool
    # this is used for loading
    is_required: bool
    # this is used for dumping
    is_optional: bool

    @staticmethod
    def _unpack_union_type(
        f: Field[_T],
    ) -> Tuple[Tuple[Type[XmlDataclass]], Optional[str], bool, bool]:
        def _unpack_list(tp: Type[Any]) -> Tuple[Type[Any], bool]:
            is_list = get_origin(tp) is list
            if is_list:
                (tp,) = get_args(tp)
            return tp, is_list

        def _unpack_union(tp: Type[Any]) -> Tuple[Type[Any]]:
            is_union = is_union_type(tp)
            if is_union:
                args: List[Type[Any]] = get_args(tp)
                return tuple(args)  # type: ignore
            return (tp,)

        if is_union_type(f.type):
            args_old: List[Type[Any]] = get_args(f.type)
            args_new = [arg for arg in args_old if arg is not NoneType]

            is_optional = len(args_old) > len(args_new)
            # as far as I know, it isn't possible to construct a single-type Union
            # if len() > 1, could have been Union[None, ...]
            if len(args_new) == 1:
                # was an Optional, unpack. list are allowed here
                tp, is_list = _unpack_list(args_new[0])
                tps = _unpack_union(tp)
            else:
                is_list = False
                tps = tuple(args_new)  # type: ignore
        else:
            is_optional = False
            tp, is_list = _unpack_list(f.type)
            tps = _unpack_union(tp)

        for tp in tps:
            if not is_xml_dataclass(tp):
                msg = (
                    f"Invalid subtype '{tp!r}' in type '{f.type!r}' on field "
                    f"'{f.name}' (child must be XML dataclass)"
                )
                raise ValueError(msg)

        # at this point, we know all types are XmlDataclass
        tps = cast(Tuple[Type[XmlDataclass]], tps)

        namespace0 = tps[0].__ns__
        for tp in tps[1:]:
            namespacen: str = tp.__ns__  # type: ignore
            if namespacen != namespace0:
                raise ValueError(
                    f"Subtype '{tp!r}' has different namespace to subtype "
                    f"'{tps[0]!r}' ('{namespacen}' != '{namespace0}')"
                )

        return tps, namespace0, is_optional, is_list

    @classmethod
    def resolve(cls: Type["ChildInfo[_T]"], f: Field[_T]) -> "ChildInfo[_T]":
        tps, namespace, is_optional, is_list = cls._unpack_union_type(f)

        rename = f.metadata.get("xml:rename")
        xml_name = format_ns(rename if rename else f.name, namespace)

        return cls(f, f.name, xml_name, tps, is_list, _is_required(f), is_optional)


@dataclass
class AttrInfo(Generic[_T]):
    field: Field[_T]
    dt_name: str
    xml_name: str
    # this is used for loading
    is_required: bool
    # this is used for dumping
    is_optional: bool

    @classmethod
    def resolve(cls: Type["AttrInfo[_T]"], f: Field[_T]) -> "AttrInfo[_T]":
        is_optional = _check_str_type(f)

        rename = f.metadata.get("xml:rename")
        namespace = f.metadata.get("xml:namespace")
        xml_name = format_ns(rename if rename else f.name, namespace)

        return cls(f, f.name, xml_name, _is_required(f), is_optional)


@dataclass
class TextInfo(Generic[_T]):
    field: Field[_T]
    dt_name: str
    # this is used for loading
    is_required: bool
    # this is used for dumping
    is_optional: bool

    @classmethod
    def resolve(cls: Type["TextInfo[_T]"], f: Field[_T]) -> "TextInfo[_T]":
        is_optional = _check_str_type(f)

        return cls(f, f.name, _is_required(f), is_optional)


def _xml_field(
    *,
    xml_type: XmlFieldType,
    default: Union[_MISSING_TYPE, _T] = MISSING,
    rename: Optional[str] = None,
    namespace: Optional[str] = None,
    metadata: Optional[Mapping[str, Any]] = None,
) -> _T:
    new_metadata: Dict[str, Any] = {"xml:type": xml_type}
    if metadata:
        new_metadata.update(metadata)
    if rename:
        new_metadata["xml:rename"] = rename
    if namespace:
        new_metadata["xml:namespace"] = namespace
    return cast(_T, field(default=default, metadata=new_metadata))


def attr(
    *,
    default: Union[_MISSING_TYPE, _T] = MISSING,
    rename: Optional[str] = None,
    namespace: Optional[str] = None,
    metadata: Optional[Mapping[str, Any]] = None,
) -> _T:
    return _xml_field(
        xml_type=XmlFieldType.Attr,
        default=default,
        rename=rename,
        namespace=namespace,
        metadata=metadata,
    )


def child(
    *,
    default: Union[_MISSING_TYPE, _T] = MISSING,
    rename: Optional[str] = None,
    metadata: Optional[Mapping[str, Any]] = None,
) -> _T:
    # the namespace of a child is set on the dataclass itself
    return _xml_field(
        xml_type=XmlFieldType.Child, default=default, rename=rename, metadata=metadata
    )


def text(
    *,
    default: Union[_MISSING_TYPE, _T] = MISSING,
    metadata: Optional[Mapping[str, Any]] = None,
) -> _T:
    # content/text can't have a namespace or rename
    return _xml_field(xml_type=XmlFieldType.Text, default=default, metadata=metadata)


class XmlDataclass:
    __ns__: Optional[str]
    __attributes__: Collection[AttrInfo[Any]]
    __children__: Collection[ChildInfo[Any]]
    __text_field__: Optional[TextInfo[Any]]
    __nsmap__: Optional[Mapping[Optional[str], str]]


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
            raise ValueError(
                f"Duplicate {self.field_type} '{xml_name}' on '{field_name}', "
                f"previously declared on '{previous}'"
            )


def xml_dataclass(cls: Type[Any]) -> Type[XmlDataclass]:
    new_cls = dataclass()(cls)
    try:
        new_cls.__ns__
    except AttributeError:
        raise ValueError("XML dataclass without namespace") from None

    try:
        new_cls.__nsmap__
    except AttributeError:
        new_cls.__nsmap__ = None

    seen_attrs = _XmlNameTracker("attribute")
    seen_children = _XmlNameTracker("child")
    attrs: List[AttrInfo[Any]] = []
    children: List[ChildInfo[Any]] = []
    text_field = None
    for f in fields(cls):
        try:
            xml_type = f.metadata["xml:type"]
        except KeyError:
            raise ValueError(f"Non-XML field '{f.name}' on XML dataclass") from None

        if xml_type == XmlFieldType.Attr:
            attr_info = AttrInfo.resolve(f)
            seen_attrs.add(attr_info.xml_name, f.name)
            attrs.append(attr_info)
        elif xml_type == XmlFieldType.Child:
            child_info = ChildInfo.resolve(f)
            seen_children.add(child_info.xml_name, f.name)
            children.append(child_info)
        elif xml_type == XmlFieldType.Text:
            text_field = TextInfo.resolve(f)
        else:
            raise ValueError(f"Unknown XML field type '{xml_type}'")

    if text_field and children:
        raise ValueError("XML dataclass with text-only content has children declared")

    new_cls.__attributes__ = attrs
    new_cls.__children__ = children
    new_cls.__text_field__ = text_field

    return new_cls
