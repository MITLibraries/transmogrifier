# ruff: noqa: PLR2004

import uuid

import pytest

import transmogrifier.models as timdex
from transmogrifier.sources.transformer import Transformer
from transmogrifier.sources.xml.datacite import Datacite


def test_transformer_get_transformer_returns_correct_class_name():
    assert Transformer.get_transformer("jpal") == Datacite


def test_transformer_get_transformer_source_missing_class_name_raises_error():
    with pytest.raises(KeyError):
        Transformer.get_transformer("cool-repo")


@pytest.mark.usefixtures("_bad_config")
def test_transformer_get_transformer_source_wrong_class_name_raises_error():
    with pytest.raises(AttributeError):
        Transformer.get_transformer("bad-class-name")


@pytest.mark.usefixtures("_bad_config")
def test_transformer_get_transformer_source_wrong_module_path_raises_error():
    with pytest.raises(ImportError):
        Transformer.get_transformer("bad-module-path")


def test_create_dates_from_publishers_success(timdex_record_required_fields):
    timdex_record_required_fields.publishers = [
        timdex.Publisher(name="Publisher", date="2018", location="Location")
    ]
    assert list(
        Transformer.create_dates_from_publishers(timdex_record_required_fields)
    ) == [timdex.Date(kind="Publication date", value="2018")]


def test_create_dates_from_publishers_drops_unparseable_dates(
    caplog, timdex_record_required_fields
):
    caplog.set_level("DEBUG")
    timdex_record_required_fields.publishers = [
        timdex.Publisher(name="Publisher", date="Date", location="Location")
    ]
    assert (
        list(Transformer.create_dates_from_publishers(timdex_record_required_fields))
        == []
    )
    assert (
        "Record ID 'cool-repo:123' has a date that couldn't be parsed: 'Date'"
        in caplog.text
    )


def test_create_locations_from_publishers_success(timdex_record_required_fields):
    timdex_record_required_fields.publishers = [
        timdex.Publisher(name="Publisher", date="2018", location="Location")
    ]
    assert list(
        Transformer.create_locations_from_publishers(timdex_record_required_fields)
    ) == [timdex.Location(value="Location", kind="Place of Publication")]


def test_create_locations_from_spatial_subjects_success(timdex_record_required_fields):
    timdex_record_required_fields.subjects = [
        timdex.Subject(value=["Some city, Some country"], kind="Dublin Core; Spatial"),
        timdex.Subject(value=["City 1", "City 2"], kind="Dublin Core; Spatial"),
    ]
    assert list(
        Transformer.create_locations_from_spatial_subjects(timdex_record_required_fields)
    ) == [
        timdex.Location(value="Some city, Some country", kind="Place Name"),
        timdex.Location(value="City 1", kind="Place Name"),
        timdex.Location(value="City 2", kind="Place Name"),
    ]


def test_transformer_run_id_explicitly_passed(generic_transformer):
    run_id = "abc123"
    transformer = generic_transformer("alma", [], run_id=run_id)
    assert transformer.run_id == run_id


def test_transformer_run_id_none_passed_generates_uuid(generic_transformer):
    transformer = generic_transformer("alma", [], run_id=None)
    assert transformer.run_id is not None
    assert uuid.UUID(transformer.run_id)
