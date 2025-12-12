# ruff: noqa: SLF001, D202
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


def test_load_exclusion_list(source_transformer, mock_s3_exclusion_list):
    source_transformer.exclusion_list_path = (
        "s3://test-bucket/libguides/config/libguides-exclusions.csv"
    )
    assert source_transformer.load_exclusion_list() == [
        "https://libguides.mit.edu/excluded1",
        "https://libguides.mit.edu/excluded2",
    ]


def test_next_iter_sets_action_skip_when_record_is_excluded(tmp_path):
    class ExcludingTransformer(Transformer):
        @classmethod
        def parse_source_file(cls, _source_file: str):
            return iter(())

        @classmethod
        def get_main_titles(cls, _source_record):
            return ["Title"]

        def get_source_link(self, source_record):
            return str(source_record["link"])

        def get_timdex_record_id(self, source_record):
            return f"cool-repo:{source_record['id']}"

        @classmethod
        def get_source_record_id(cls, source_record):
            return str(source_record["id"])

        @classmethod
        def record_is_deleted(cls, _source_record):
            return False

        def record_is_excluded(self, source_record):
            source_link = self.get_source_link(source_record)
            return source_link in (self.exclusion_list or [])

    exclusion_list_path = tmp_path / "exclusions.csv"
    exclusion_list_path.write_text("https://example.com/exclude-me\n")
    transformer = ExcludingTransformer(
        "cool-repo",
        iter([{"id": "123", "link": "https://example.com/exclude-me"}]),
        exclusion_list_path=str(exclusion_list_path),
    )

    dataset_record = next(transformer)
    assert dataset_record.action == "skip"
    assert dataset_record.transformed_record is None
    assert json.loads(dataset_record.source_record) == {
        "id": "123",
        "link": "https://example.com/exclude-me",
    }


def test_transformer_get_transformer_returns_correct_class_name():
    assert Transformer.get_transformer("jpal") == Datacite


def test_transformer_get_transformer_source_missing_class_name_raises_error():
    with pytest.raises(KeyError):
        Transformer.get_transformer("wrong-repo")


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
    source_transformer, source_input_file, run_id
):
    assert source_transformer.get_run_data(source_input_file, run_id) == {
        "source": "libguides",
        "run_date": "2024-06-03",
        "run_type": "full",
        "run_id": run_id,
        "run_timestamp": "2024-06-03T00:00:00",
    }


def test_transformer_get_run_data_with_explicit_run_timestamp(
    source_transformer, source_input_file, run_id
):
    run_timestamp = "2024-06-03T15:30:45"
    assert source_transformer.get_run_data(
        source_input_file,
        run_id=run_id,
        run_timestamp=run_timestamp,
    ) == {
        "source": "libguides",
        "run_date": "2024-06-03",
        "run_type": "full",
        "run_id": run_id,
        "run_timestamp": run_timestamp,
    }


def test_transformer_get_run_data_mints_timestamp_from_run_date(
    source_transformer, source_input_file, run_id
):
    result = source_transformer.get_run_data(source_input_file, run_id)
    assert result["run_timestamp"] == "2024-06-03T00:00:00"


def test_transformer_get_run_data_no_source_file_raise_error(
    monkeypatch, source_transformer
):
    monkeypatch.setenv("WORKSPACE", "dev")
    with pytest.raises(
        ValueError,
        match="'source_file' parameter is required outside of test environments",
    ):
        source_transformer.get_run_data(None, "run-abc-123")


def test_transformer_next_iter_yields_dataset_records(source_transformer):
    assert isinstance(next(source_transformer), DatasetRecord)


def test_transform_next_iter_sets_valid_source_and_transformed_records(
    source_transformer,
):
    record = next(source_transformer)

    # parse source record XML
    assert isinstance(record.source_record, bytes)
    source_record = etree.fromstring(record.source_record)
    assert isinstance(source_record, etree._Element)

    # parse transformed record
    assert isinstance(record.transformed_record, bytes)
    transformed_record = json.loads(record.transformed_record)
    assert isinstance(transformed_record, dict)


def test_transform_next_iter_uses_run_data_parsed_from_source_file(
    source_transformer, source_input_file, run_id
):
    record = next(source_transformer)
    run_data = source_transformer.get_run_data(source_input_file, run_id)
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
    source_transformer, transform_exception, expected_action
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
        with mock.patch.object(source_transformer, "transform") as mocked_transform:
            mocked_transform.side_effect = transform_exception
            record = next(source_transformer)
            assert mocked_transform.called
    else:
        record = next(source_transformer)
    assert record.action == expected_action


def test_transformer_provenance_object_added_to_transformed_record(source_transformer):
    dataset_record = next(source_transformer)
    transformed_record = json.loads(dataset_record.transformed_record)
    assert transformed_record["timdex_provenance"] == {
        "source": "libguides",
        "run_date": "2024-06-03",
        "run_id": "run-abc-123",
        "run_record_offset": 0,
    }


def test_transformer_provenance_object_run_record_offset_increments(
    source_transformer,
):
    for i in range(4):
        dataset_record = next(source_transformer)
        if dataset_record.action != "index":
            continue
        transformed_record = json.loads(dataset_record.transformed_record)
        assert transformed_record["timdex_provenance"]["run_record_offset"] == i


def test_transformer_load_with_run_timestamp_parameter(
    source_transformer_with_timestamp, source_input_file, run_id
):
    assert source_transformer_with_timestamp.run_data == {
        "source": "libguides",
        "run_date": "2024-06-03",
        "run_type": "full",
        "run_id": run_id,
        "run_timestamp": "2024-06-03T15:30:45",
    }


def test_transformer_load_without_run_timestamp_parameter(
    source_transformer, source_input_file, run_id
):
    assert source_transformer.run_data == {
        "source": "libguides",
        "run_date": "2024-06-03",
        "run_type": "full",
        "run_id": run_id,
        "run_timestamp": "2024-06-03T00:00:00",
    }


def test_transformer_dataset_write_includes_run_timestamp_column(
    tmp_path,
    source_transformer,
):
    dataset_location = tmp_path / "dataset"
    written_files = source_transformer.write_to_parquet_dataset(str(dataset_location))

    parquet_file = written_files[0]
    assert "run_timestamp" in parquet_file.metadata.schema.names
