# XML dataclasses

[![License: MPL 2.0](https://img.shields.io/badge/License-MPL%202.0-brightgreen.svg)](https://opensource.org/licenses/MPL-2.0) ![Build](https://github.com/tobywf/xml_dataclasses/workflows/Build/badge.svg?branch=master)

[XML dataclasses on PyPI](https://pypi.org/project/xml-dataclasses/)

This library maps XML to and from Python dataclasses. It build on normal dataclasses from the standard library and uses [`lxml`](https://pypi.org/project/lxml/) for parsing/generating XML.

It's currently in alpha. It isn't ready for production if you aren't willing to do your own evaluation/quality assurance.

Requires Python 3.7 or higher.

## Features

* Convert XML documents to well-defined dataclasses, which work with Mypy or IDE auto-completion
* XML dataclasses are dataclasses
* Full control of parsing and generating XML via `lxml`
* Loading and dumping of attributes, child elements, and text content
* Required and optional attributes/child elements
* Lists of child elements are supported, as are unions and lists or unions
* Inheritance does work, but has the same limitations as dataclasses. Inheriting from base classes with required fields and declaring optional fields doesn't work due to field order. This isn't recommended
* Namespace support is decent as long as correctly declared. I've tried on several real-world examples, although they were known to be valid. `lxml` does a great job at expanding namespace information when loading and simplifying it when saving
* Post-load validation hook `xml_validate`
* Fields not required in the constructor are ignored by this library (via `ignored()` or `init=False`)

## Limitations

* Whitespace and comments aren't supported in the data model. They must be stripped when loading the XML
* So far, I haven't found any examples where XML can't be mapped to a dataclass, but it's likely possible given how complex XML is
* No typing/type conversions. Since XML is untyped, only string values are currently allowed. Type conversions are tricky to implement in a type-safe and extensible manner.
* Dataclasses must be written by hand, no tools are provided to generate these from, DTDs, XML schema definitions, or RELAX NG schemas

## Security

The caveats concerning untrusted content are roughly the same as with `lxml`, since that does the parsing. This is good, since `lxml`'s behaviour to XML attacks are well-understood. This library recursively resolves data structures, which may have memory implications for unbounded payloads. Because loading is driven from the dataclass definitions, it shouldn't be possible to execute arbitrary Python code (not a guarantee, see license). If you must deal with untrusted content, a workaround is to [use `lxml` to validate](https://lxml.de/validation.html) untrusted content with a strict schema, which you may already be doing.

## Patterns

### Defining attributes

Attributes can be either `str` or `Optional[str]`. Using any other type won't work. Attributes can be renamed or have their namespace modified via the `rename` function. It can be used either on its own, or with an existing field definition:

```python
@xml_dataclass
class Foo:
    __ns__ = None
    required: str
    optional: Optional[str] = None
    renamed_with_default: str = rename(default=None, name="renamed-with-default")
    namespaced: str = rename(ns="http://www.w3.org/XML/1998/namespace")
    existing_field: str = rename(field(...), name="existing-field")
```

For now, you can work around this limitation with properties that do the conversion, and perform post-load validation.

By default, unknown attributes raise an error. This can be disabled by passing `Options` to `load` with `ignore_unknown_attributes`.

### Defining text

Like attributes, text can be either `str` or `Optional[str]`. You must declare text content with the `text` function. Similar to `rename`, this function can use an existing field definition, or take the `default` argument. Text cannot be renamed or namespaced. Every class can only have one field defining text content. If a class has text content, it cannot have any children.

```python
@xml_dataclass
class Foo:
    __ns__ = None
    value: str = text()

@xml_dataclass
class Foo:
    __ns__ = None
    content: Optional[str] = text(default=None)

@xml_dataclass
class Foo:
    __ns__ = None
    uuid: str = text(field(default_factory=lambda: str(uuid4())))
```

### Defining children/child elements

Children must ultimately be other XML dataclasses. However, they can also be `Optional`, `List`, and `Union` types:

* `Optional` must be at the top level. Valid: `Optional[List[XmlDataclass]]`. Invalid: `List[Optional[XmlDataclass]]`
* Next, `List` should be defined (if multiple child elements are allowed). Valid: `List[Union[XmlDataclass1, XmlDataclass2]]`. Invalid: `Union[List[XmlDataclass1], XmlDataclass2]`
* Finally, if `Optional` or `List` were used, a union type should be the inner-most (again, if needed)

If a class has children, it cannot have text content.

Children can be renamed via the `rename` function. However, attempting to set a namespace is invalid, since the namespace is provided by the child type's XML dataclass. Also, unions of XML dataclasses must have the same namespace (you can use different fields with renaming if they have different namespaces, since the XML names will be resolved as a combination of namespace and name).

By default, unknown children raise an error. This can be disabled by passing `Options` to `load` with `ignore_unknown_children`.

### Defining post-load validation

Simply implement an instance method called `xml_validate` with no parameters, and no return value (if you're using type hints):

```python
def xml_validate(self) -> None:
    pass
```

If defined, the `load` function will call it after all values have been loaded and assigned to the XML dataclass. You can validate the fields you want inside this method. Return values are ignored; instead raise and catch exceptions.

### Ignored fields

Fields not required in the constructor are ignored by this library (new in version 0.0.6). This is useful if you want to populate a field via post-load validation.

You can simply set `init=False`, although you may also want to exclude the field from comparisons. The `ignored` function does this, and can also be used.

The name doesn't matter, but it might be useful to use the `_` prefix as a convention.

## Example (fully type hinted)

(This is a simplified real world example - the container can also include optional `links` child elements.)

```xml
<?xml version="1.0"?>
<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">
  <rootfiles>
    <rootfile full-path="OEBPS/content.opf" media-type="application/oebps-package+xml" />
  </rootfiles>
</container>
```

```python
from dataclasses import dataclass
from typing import List
from lxml import etree  # type: ignore
from xml_dataclasses import xml_dataclass, rename, load, dump, NsMap, XmlDataclass

CONTAINER_NS = "urn:oasis:names:tc:opendocument:xmlns:container"


@xml_dataclass
@dataclass
class RootFile:
    __ns__ = CONTAINER_NS
    full_path: str = rename(name="full-path")
    media_type: str = rename(name="media-type")


@xml_dataclass
@dataclass
class RootFiles:
    __ns__ = CONTAINER_NS
    rootfile: List[RootFile]


# see Gotchas, this workaround is required for type hinting
@xml_dataclass
@dataclass
class Container(XmlDataclass):
    __ns__ = CONTAINER_NS
    version: str
    rootfiles: RootFiles
    # WARNING: this is an incomplete implementation of an OPF container

    def xml_validate(self) -> None:
        if self.version != "1.0":
            raise ValueError(f"Unknown container version '{self.version}'")


if __name__ == "__main__":
    nsmap: NsMap = {None: CONTAINER_NS}
    # see Gotchas, stripping whitespace and comments is highly recommended
    parser = etree.XMLParser(remove_blank_text=True, remove_comments=True)
    lxml_el_in = etree.parse("container.xml", parser).getroot()
    container = load(Container, lxml_el_in, "container")
    lxml_el_out = dump(container, "container", nsmap)
    print(etree.tostring(lxml_el_out, encoding="unicode", pretty_print=True))
```

## Gotchas

### Type hinting

This can be a real pain to get right. Unfortunately, if you need this, you may have to resort to:

```python
@xml_dataclass
@dataclass
class Child:
    __ns__ = None
    pass

@xml_dataclass
@dataclass
class Parent(XmlDataclass):
    __ns__ = None
    children: Child
```

It's important that `@dataclass` be the *last* decorator, i.e. the closest to the class definition (and so the first to be applied). Luckily, only the root class you intend to pass to `load`/`dump` has to inherit from `XmlDataclass`, but all classes should have the `@dataclass` decorator applied.

### Whitespace and comments

If you are able to, it is strongly recommended you strip whitespace and comments from the input via `lxml`:

```python
parser = etree.XMLParser(remove_blank_text=True, remove_comments=True)
```

By default, `lxml` preserves whitespace. This can cause a problem when checking if elements have no text. The library does attempt to strip these; literally via Python's `strip()`. But `lxml` is likely faster and more robust.

Similarly, comments are included by default, and because loading is strict, they will be considered as nodes that the dataclass has not declared. It is recommended to omit them during parsing.

### Optional vs required

On dataclasses, optional fields also usually have a default value to be useful. But this isn't required; `Optional` is just a type hint to say `None` is allowed. This would occur e.g. if an element has no children.

For loading XML dataclasses, whether or not a field is required is determined by if it has a `default`/`default_factory` defined. If so, and it's missing, that default is used. Otherwise, an error is raised.

For dumping, the default isn't considered. Instead, if a value is marked as `Optional` and the value is `None`, it isn't written.

This makes sense in many cases, but possibly not every case.

## Changelog

### [0.0.9] - 2022-02-10

* Fix issue passing options when loading children - thanks [tim-lansen](https://github.com/tim-lansen)!

### [0.0.7] and [0.0.8] - 2021-04-08

* Warn if comments are found/don't treat comments as child elements in error messages
* Allow lenient loading of undeclared attributes or children

### [0.0.6] - 2020-03-25

* Allow ignored fields via `init=false` or the `ignored` function

### [0.0.5] - 2020-02-18

* Fixed type hinting for consumers. While the library passed mypy validation, it was hard to get XML dataclasses in a codebase to pass mypy validation

### [0.0.4] - 2020-02-16

* Improved type resolving. This lead to easier field definitions, as `attr` and `child` are no longer needed because the type of the field is inferred

### [0.0.3] - 2020-02-16

* Added support for union types on children

## Development

This project uses [pre-commit](https://pre-commit.com/) to run some linting hooks when committing. When you first clone the repo, please run:

```
pre-commit install
```

You may also run the hooks at any time:

```
pre-commit run --all-files
```

Dependencies are managed via [poetry](https://python-poetry.org/). To install all dependencies, use:

```
poetry install
```

This will also install development dependencies such as `black`, `isort`, `pylint`, `mypy`, and `pytest`. Pre-defined tasks make it easy to run these, for example

* `poetry run task lint` - this runs `black`, `isort`, `mypy`, and `pylint`
* `poetry run task test` - this runs `pytest` with coverage

For a full list of tasks, see `poetry run task --list`.

## License

This library is licensed under the Mozilla Public License Version 2.0. For more information, see `LICENSE`.
