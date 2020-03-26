from __future__ import annotations

from dataclasses import MISSING, Field, field
from itertools import combinations

import pytest

from xml_dataclasses.modifiers import ignored, rename, text


def dict_comb(items, r=2):
    return [{**a, **b} for a, b in combinations(items, r)]


DEFAULTS = [MISSING, None, "bar"]


def test_rename_no_field_no_default():
    f = rename()
    assert isinstance(f, Field)
    assert f.default is MISSING
    assert f.metadata == {}


@pytest.mark.parametrize("default", DEFAULTS)
def test_rename_no_field_default(default):
    f = rename(default=default)
    assert isinstance(f, Field)
    assert f.default is default
    assert f.metadata == {}


@pytest.mark.parametrize("default", DEFAULTS)
def test_rename_has_field_default_ignored(default):
    expected_field = field(metadata={"foo": "bar"})
    expected_md = dict(expected_field.metadata)

    actual_field = rename(expected_field, default=default)
    assert actual_field is expected_field
    assert actual_field.default is MISSING
    assert actual_field.metadata == expected_md


@pytest.mark.parametrize("kwargs", dict_comb(({}, {"name": "bar"}, {"ns": "bar"})))
def test_rename_no_metadata(kwargs):
    actual_field = rename(field(), **kwargs)
    expected_md = {f"xml:{k}": v for k, v in kwargs.items()}
    assert actual_field.metadata == expected_md


@pytest.mark.parametrize("kwargs", dict_comb(({}, {"name": "bar"}, {"ns": "bar"})))
def test_rename_has_metadata(kwargs):
    expected_field = field(metadata={"foo": "bar"})
    expected_md = dict(expected_field.metadata)
    expected_md.update({f"xml:{k}": v for k, v in kwargs.items()})

    actual_field = rename(expected_field, **kwargs)
    assert actual_field.metadata == expected_md


def test_text_no_field_no_default():
    f = text()
    assert isinstance(f, Field)
    assert f.default is MISSING
    assert f.metadata == {"xml:text": True}


@pytest.mark.parametrize("default", DEFAULTS)
def test_text_no_field_default(default):
    f = text(default=default)
    assert isinstance(f, Field)
    assert f.default is default
    assert f.metadata == {"xml:text": True}


@pytest.mark.parametrize("default", DEFAULTS)
def test_text_has_field_default_ignored(default):
    expected_field = field(metadata={"foo": "bar"})
    expected_md = {**expected_field.metadata, "xml:text": True}

    actual_field = text(expected_field, default=default)
    assert actual_field is expected_field
    assert actual_field.default is MISSING
    assert actual_field.metadata == expected_md


def test_ignored_field():
    actual_field = ignored()
    assert not actual_field.init
    assert not actual_field.compare
