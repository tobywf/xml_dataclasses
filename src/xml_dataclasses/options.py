from dataclasses import dataclass


@dataclass
class Options:
    ignore_unknown_attributes: bool = False
    ignore_unknown_children: bool = False
