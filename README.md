# XML dataclasses

This is a very rough prototype of how a library might look like for (de)serialising XML into  Python dataclasses. XML dataclasses build on normal dataclasses from the standard library and [`lxml`](https://pypi.org/project/lxml/) elements. Loading and saving these elements is left to the consumer for flexibility of the desired output.

It isn't ready for production if you aren't willing to do your own evaluation/quality assurance. I don't recommend using this library with untrusted content. It inherits all of `lxml`'s flaws with regards to XML attacks, and recursively resolves data structures. Because deserialisation is driven from the dataclass definitions, it shouldn't be possible to execute arbitrary Python code. But denial of service attacks would very likely be feasible.

Requires Python 3.7 or higher.

## Example

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
from lxml import etree
from typing import List
from xml_dataclasses import xml_dataclass, attr, child, load, dump

CONTAINER_NS = "urn:oasis:names:tc:opendocument:xmlns:container"

@xml_dataclass
class RootFile:
    __ns__ = CONTAINER_NS
    full_path: str = attr(rename="full-path")
    media_type: str = attr(rename="media-type")


@xml_dataclass
class RootFiles:
    __ns__ = CONTAINER_NS
    rootfile: List[RootFile] = child()


@xml_dataclass
class Container:
    __ns__ = CONTAINER_NS
    version: str = attr()
    rootfiles: RootFiles = child()
    # WARNING: this is an incomplete implementation of an OPF container
    # (it's missing links)


if __name__ == "__main__":
    nsmap = {None: CONTAINER_NS}
    lxml_el_in = etree.parse("container.xml").getroot()
    container = load(Container, lxml_el_in, "container")
    lxml_el_out = dump(container, "container", nsmap)
    print(etree.tostring(lxml_el_out, encoding="unicode", pretty_print=True))
```

## Features

* XML dataclasses are also dataclasses, and only require a single decorator
* Convert XML documents to well-defined dataclasses, which should work with IDE auto-completion
* Loading and dumping of attributes, child elements, and text content
* Required and optional attributes and child elements
* Lists of child elements are supported
* Inheritance does work, but has the same limitations as dataclasses. Inheriting from base classes with required fields and declaring optional fields doesn't work due to field order. This isn't recommended
* Namespace support is decent as long as correctly declared. I've tried on several real-world examples, although they were known to be valid. `lxml` does a great job at expanding namespace information when loading and simplifying it when saving

## Limitations and Assumptions

Most of these limitations/assumptions are enforced. They may make this project unsuitable for your use-case.

* All attributes are strings, no extra validation is performed. I would like to add support for validation in future, which might also make it easier to support other types
* Elements can either have child elements or text content, not both
* Child elements are other XML dataclasses
* Text content is a string
* It isn't possible to pass any parameters to the wrapped `@dataclass` decorator
* Some properties of dataclass `field`s are not exposed: `default_factory`, `repr`, `hash`, `init`, `compare`. For most, it is because I don't understand the implications fully or how that would be useful for XML. `default_factory` is hard only because of [the overloaded type signatures](https://github.com/python/typeshed/blob/master/stdlib/3.7/dataclasses.pyi), and getting that to work with `mypy`
* Deserialisation is strict; missing required attributes and child elements will cause an error
* Unions of types aren't yet supported
* Dataclasses must be written by hand, no tools are provided to generate these from, DTDs, XML schema definitions, or RELAX NG schemas

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

This will also install development dependencies such as `black`, `isort`, `pylint`, `mypy`, and `pytest`. I've provided a simple script to run these during development called `lint`. You can either run it from a shell session with the poetry-installed virtual environment, or run as follows:

```
poetry run ./lint
```

Auto-formatters will be applied, and static analysis/tests are run in order. The script stops on failure to allow quick iteration.

## License

This library is licensed under the Mozilla Public License Version 2.0. For more information, see `LICENSE`.
