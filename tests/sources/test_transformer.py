# ruff: noqa: PLR2004, SLF001, D202
import datetime
import json
from unittest import mock

import pytest
from lxml import etree
from timdex_dataset_api.record import DatasetRecord

import transmogrifier.models as timdex
from transmogrifier.exceptions import DeletedRecordEvent, SkippedRecordEvent
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


def test_transformer_get_run_data_from_source_file_and_run_id(
    libguides_transformer, libguides_input_file, run_id
):
    assert libguides_transformer.get_run_data(libguides_input_file, run_id) == {
        "source": "libguides",
        "run_date": "2024-06-03",
        "run_type": "full",
        "run_id": run_id,
    }


def test_transformer_next_iter_yields_dataset_records(libguides_transformer):
    assert isinstance(next(libguides_transformer), DatasetRecord)


def test_transform_next_iter_sets_valid_source_and_transformed_records(
    libguides_transformer,
):
    record = next(libguides_transformer)

    # parse source record XML
    assert isinstance(record.source_record, bytes)
    source_record = etree.fromstring(record.source_record)
    assert isinstance(source_record, etree._Element)

    # parse transformed record
    assert isinstance(record.transformed_record, bytes)
    transformed_record = json.loads(record.transformed_record)
    assert isinstance(transformed_record, dict)


def test_transform_next_iter_uses_run_data_parsed_from_source_file(
    libguides_transformer, libguides_input_file, run_id
):
    record = next(libguides_transformer)
    run_data = libguides_transformer.get_run_data(libguides_input_file, run_id)
    assert (
        record.run_date
        == datetime.datetime.strptime(run_data["run_date"], "%Y-%m-%d")
        .astimezone(datetime.UTC)
        .date()
    )
    assert record.run_type == run_data["run_type"]
    assert record.run_id == run_id


@pytest.mark.parametrize(
    ("transform_exception", "expected_action"),
    [
        (None, "index"),
        (DeletedRecordEvent(timdex_record_id="libguides:guides-0"), "delete"),
        (SkippedRecordEvent(source_record_id="guides-0"), "skip"),
        (RuntimeError("totally unhandled event"), "error"),
    ],
)
def test_transformer_action_column_based_on_transformation_exception_handling(
    libguides_transformer, transform_exception, expected_action
):
    """While Transmogrifier is often considered just an application to transform a source
    record into a TIMDEX record, it also serves the purpose of determining if a source
    record should be indexed or deleted, or skipped (no action taken), or handling when a
    record cannot be transformed (unhandled error).  This 'action' that Transmogrifier
    determines for each record is captured in the 'action' column in the TIMDEX parquet
    dataset.

    This test ensures that the 'action' column values are correct given behavior
    (exception handling) during transformation of each record.
    """

    if transform_exception:
        with mock.patch.object(libguides_transformer, "transform") as mocked_transform:
            mocked_transform.side_effect = transform_exception
            record = next(libguides_transformer)
            assert mocked_transform.called
    else:
        record = next(libguides_transformer)
    assert record.action == expected_action


def test_transformer_provenance_object_added_to_transformed_record(libguides_transformer):
    dataset_record = next(libguides_transformer)
    transformed_record = json.loads(dataset_record.transformed_record)
    assert transformed_record["timdex_provenance"] == {
        "source": "libguides",
        "run_date": "2024-06-03",
        "run_id": "run-abc-123",
        "run_record_offset": 0,
    }


def test_transformer_provenance_object_run_record_offset_increments(
    libguides_transformer,
):
    for i in range(4):
        dataset_record = next(libguides_transformer)
        if dataset_record.action != "index":
            continue
        transformed_record = json.loads(dataset_record.transformed_record)
        assert transformed_record["timdex_provenance"]["run_record_offset"] == i
