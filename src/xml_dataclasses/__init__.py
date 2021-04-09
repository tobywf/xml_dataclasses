import logging

logging.getLogger(__name__).addHandler(logging.NullHandler())

from .options import Options  # isort:skip
from .modifiers import rename, text, ignored  # isort:skip
from .resolve_types import (  # isort:skip
    is_xml_dataclass,
    xml_dataclass,
    NsMap,
    XmlDataclass,
)
from .serde import dump, load  # isort:skip


# __all__ is required for mypy to pick up the imports
# for errors, use `from xml_dataclasses.errors import ...`
__all__ = [
    "rename",
    "text",
    "dump",
    "load",
    "is_xml_dataclass",
    "xml_dataclass",
    "NsMap",
    "XmlDataclass",
    "ignored",
]
