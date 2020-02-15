from typing import Optional, Tuple


def format_ns(name: str, namespace: Optional[str]) -> str:
    if namespace:
        return f"{{{namespace}}}{name}"
    return name


def strip_ns(tag: str) -> Tuple[str, Optional[str]]:
    if not tag:
        raise ValueError("Empty tag")
    if tag[0] == "{":
        namespace, _, name = tag[1:].partition("}")
        return name, namespace
    return tag, None
