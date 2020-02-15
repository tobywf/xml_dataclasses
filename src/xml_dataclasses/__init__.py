import logging

logging.getLogger(__name__).addHandler(logging.NullHandler())

from .structs import attr, child, text, xml_dataclass  # isort:skip
from .serde import dump, load  # isort:skip
