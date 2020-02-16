class XmlDataclassError(Exception):
    pass


class XmlDataclassInternalError(XmlDataclassError):
    pass


class XmlDataclassNoNamespaceError(XmlDataclassError):
    MESSAGE = "XML dataclass without namespace"

    def __init__(self) -> None:
        super().__init__(self.MESSAGE)


class XmlDataclassModelError(XmlDataclassError):
    pass


class XmlDataclassContentsError(XmlDataclassModelError):
    MESSAGE = "XML dataclass with text-only content has children declared"

    def __init__(self) -> None:
        super().__init__(self.MESSAGE)


class XmlDataclassDuplicateFieldError(XmlDataclassModelError):
    pass


class XmlTypeError(XmlDataclassModelError):
    pass
