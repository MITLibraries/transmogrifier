# ruff: noqa: SLF001, D202
import datetime
import json
from pathlib import Path
from unittest import mock

import pyarrow as pa
import pyarrow.parquet as pq
import pytest
from bs4 import Tag
from lxml import etree
from timdex_dataset_api import DatasetRecord

import transmogrifier.models as timdex
from transmogrifier.exceptions import DeletedRecordEvent, SkippedRecordEvent
from transmogrifier.sources import transformer as transformer_module
from transmogrifier.sources.json.aardvark import MITAardvark
from transmogrifier.sources.jsontransformer import JSONTransformer
from transmogrifier.sources.transformer import PARQUET_FILES_SCHEMA, Transformer
from transmogrifier.sources.xml.datacite import Datacite
from transmogrifier.sources.xmltransformer import XMLTransformer


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
        def read_source_file(cls, _source_file: str):
            return iter(())

        @classmethod
        def parse_source_record(cls, source_record: bytes):
            return json.loads(source_record)

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
    mocked_datetime = mock.MagicMock()
    mocked_datetime.now.return_value.isoformat.return_value = "2024-06-03T12:34:56+00:00"
    with mock.patch("transmogrifier.sources.transformer.datetime", mocked_datetime):
        assert source_transformer.get_run_data(
            "libguides", source_input_file, run_id=run_id
        ) == {
            "source": "libguides",
            "run_date": "2024-06-03",
            "run_type": "full",
            "run_id": run_id,
            "run_timestamp": "2024-06-03T12:34:56+00:00",
        }


def test_transformer_get_run_data_with_explicit_run_timestamp(
    source_transformer, source_input_file, run_id
):
    run_timestamp = "2024-06-03T15:30:45"
    assert source_transformer.get_run_data(
        "libguides",
        source_file=source_input_file,
        run_id=run_id,
        run_timestamp=run_timestamp,
    ) == {
        "source": "libguides",
        "run_date": "2024-06-03",
        "run_type": "full",
        "run_id": run_id,
        "run_timestamp": run_timestamp,
    }


def test_transformer_get_run_data_mints_current_utc_timestamp(
    source_transformer, source_input_file, run_id
):
    mocked_datetime = mock.MagicMock()
    mocked_datetime.now.return_value.isoformat.return_value = "2024-06-03T12:34:56+00:00"
    with mock.patch("transmogrifier.sources.transformer.datetime", mocked_datetime):
        result = source_transformer.get_run_data(
            "cool-repo", source_file=source_input_file, run_id=run_id
        )
    assert result["run_timestamp"] == "2024-06-03T12:34:56+00:00"


def test_transformer_get_run_data_multi_input_source_raise_error(
    monkeypatch, source_transformer
):
    monkeypatch.setenv("WORKSPACE", "dev")
    with pytest.raises(
        ValueError,
        match="Exactly one input source is required: 'source_file', 'source_dataset', "
        "or 'source_parquet'",
    ):
        source_transformer.get_run_data(
            "cool-repo", source_file="abc", source_dataset="def", run_id="run-abc-123"
        )


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
    run_data = source_transformer.get_run_data(
        "cool-repo", source_file=source_input_file, run_id=run_id
    )
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
        "run_timestamp": "2024-06-03T12:34:56+00:00",
    }


def test_transformer_dataset_write_includes_run_timestamp_column(
    tmp_path,
    source_transformer,
):
    dataset_location = tmp_path / "dataset"
    written_files = source_transformer.write_to_timdex_dataset(str(dataset_location))

    parquet_file = written_files[0]
    assert "run_timestamp" in parquet_file.metadata.schema.names


def test_xmltransformer_parse_source_record_returns_tag():
    record = XMLTransformer.parse_source_record(b"<record><title>Hi</title></record>")
    assert isinstance(record, Tag)
    assert record.find("title").string == "Hi"


def test_jsontransformer_parse_source_record_returns_dict():
    assert JSONTransformer.parse_source_record(b'{"id": "123"}') == {"id": "123"}


def test_jsontransformer_parse_source_record_non_dict_raises_error():
    with pytest.raises(TypeError, match="Expected JSON source record to be a dict"):
        JSONTransformer.parse_source_record(b"[1, 2, 3]")


def test_transformer_read_source_records_from_dataset_yields_bytes():
    with mock.patch(
        "transmogrifier.sources.transformer.TIMDEXDataset"
    ) as mocked_dataset_class:
        mocked_records = mocked_dataset_class.return_value.records
        mocked_records.read_dicts_iter.return_value = iter(
            [
                {"source": "cool-repo", "source_record": b'{"id": "1"}'},
                {"source": "cool-repo", "source_record": b'{"id": "2"}'},
            ]
        )
        records = list(
            JSONTransformer.read_source_records_from_dataset(
                "cool-repo", "s3://bucket/dataset"
            )
        )

    assert records == [b'{"id": "1"}', b'{"id": "2"}']
    mocked_dataset_class.assert_called_once_with("s3://bucket/dataset")
    mocked_records.read_dicts_iter.assert_called_once_with(
        table="current_records",
        columns=["source_record"],
        source="cool-repo",
        action="index",
    )


def test_transformer_get_run_data_from_source_parquet_sets_patch_run_type(run_id):
    run_data = Transformer.get_run_data(
        "alma", source_parquet="path/to/export", run_id=run_id
    )
    assert run_data["source"] == "alma"
    assert run_data["run_type"] == "patch"
    assert run_data["run_id"] == run_id


def test_transformer_load_multiple_input_sources_raises_error(source_input_file):
    with pytest.raises(ValueError, match="Exactly one input source is required"):
        Transformer.load(
            "cool-repo", source_file=source_input_file, source_parquet="path/to/export"
        )


def test_transformer_load_from_source_parquet(tmp_path, source_parquet_location):
    transformer = Transformer.load(
        "researchdatabases", source_parquet=source_parquet_location
    )
    assert transformer.source_parquet == source_parquet_location
    assert transformer.run_data["run_type"] == "patch"
    assert next(transformer).action == "index"


def test_transformer_read_source_records_from_parquet_filters_source_and_action(
    tmp_path,
):
    pq.write_table(
        pa.Table.from_pylist(
            [
                {
                    "source_record": b'{"id": "1"}',
                    "source": "cool-repo",
                    "action": "index",
                },
                {"source_record": b'{"id": "2"}', "source": "other", "action": "index"},
                {
                    "source_record": b'{"id": "3"}',
                    "source": "cool-repo",
                    "action": "delete",
                },
                {
                    "source_record": b'{"id": "4"}',
                    "source": "cool-repo",
                    "action": "index",
                },
            ]
        ),
        tmp_path / "records.parquet",
    )
    records = list(
        JSONTransformer.read_source_records_from_parquet(
            "cool-repo", str(tmp_path / "records.parquet")
        )
    )
    assert records == [b'{"id": "1"}', b'{"id": "4"}']


def test_transformer_read_source_records_from_parquet_directory_in_path_order(
    tmp_path,
):
    data_dir = tmp_path / "export" / "data"
    data_dir.mkdir(parents=True)
    (tmp_path / "export" / "export.json").write_text("{}")
    for i in (1, 0):
        pq.write_table(
            pa.Table.from_pylist(
                [
                    {
                        "source_record": f'{{"id": "{i}"}}'.encode(),
                        "source": "cool-repo",
                        "action": "index",
                    }
                ]
            ),
            data_dir / f"part-{i:05d}.parquet",
        )
    records = list(
        JSONTransformer.read_source_records_from_parquet(
            "cool-repo", str(tmp_path / "export")
        )
    )
    assert records == [b'{"id": "0"}', b'{"id": "1"}']


def test_transformer_write_to_parquet_files_matches_timmy_export_layout(
    tmp_path, source_transformer
):
    written_files = source_transformer.write_to_parquet_files(str(tmp_path / "output"))

    assert [Path(f).name for f in written_files] == ["part-0.parquet"]
    parquet_file = pq.ParquetFile(written_files[0])
    assert parquet_file.schema_arrow.equals(PARQUET_FILES_SCHEMA)
    assert parquet_file.metadata.row_group(0).column(0).compression == "ZSTD"

    rows = parquet_file.read().to_pylist()
    assert [row["run_record_offset"] for row in rows] == list(range(len(rows)))
    index_row = next(row for row in rows if row["action"] == "index")
    transformed_record = json.loads(index_row["transformed_record"])
    assert transformed_record["timdex_record_id"] == index_row["timdex_record_id"]


def test_transformer_write_to_parquet_files_splits_files_in_run_order(
    monkeypatch, tmp_path, source_transformer
):
    monkeypatch.setattr(transformer_module, "PARQUET_FILES_MAX_ROWS_PER_FILE", 2)
    monkeypatch.setattr(transformer_module, "PARQUET_FILES_ROW_GROUP_SIZE", 2)
    written_files = source_transformer.write_to_parquet_files(str(tmp_path / "output"))

    row_counts = [pq.ParquetFile(f).metadata.num_rows for f in written_files]
    assert len(written_files) > 1
    assert all(count <= 2 for count in row_counts)  # noqa: PLR2004
    offsets = [
        offset
        for f in sorted(written_files)
        for offset in pq.read_table(f).column("run_record_offset").to_pylist()
    ]
    assert offsets == list(range(sum(row_counts)))


def test_transformer_write_to_parquet_files_non_empty_output_raises_error(
    tmp_path, source_transformer
):
    output_location = tmp_path / "output"
    output_location.mkdir()
    pq.write_table(pa.table({"a": [1]}), output_location / "part-00000.parquet")
    with pytest.raises(ValueError, match="directory is not empty"):
        source_transformer.write_to_parquet_files(str(output_location))


def test_transformer_parquet_files_round_trip_preserves_transformed_records(
    tmp_path, source_parquet_location
):
    original_rows = pq.read_table(source_parquet_location).to_pylist()
    transformer = Transformer.load(
        "researchdatabases", source_parquet=source_parquet_location
    )
    written_files = transformer.write_to_parquet_files(str(tmp_path / "round_trip"))
    round_trip_rows = pq.read_table(written_files[0]).to_pylist()

    def without_provenance(row: dict) -> dict:
        record = json.loads(row["transformed_record"])
        record.pop("timdex_provenance")
        return record

    original_indexed = [row for row in original_rows if row["action"] == "index"]
    assert [row["timdex_record_id"] for row in round_trip_rows] == [
        row["timdex_record_id"] for row in original_indexed
    ]
    assert [without_provenance(row) for row in round_trip_rows] == [
        without_provenance(row) for row in original_indexed
    ]


def test_transformer_write_to_file_writes_only_indexed_records(
    tmp_path, source_transformer
):
    output_file = tmp_path / "records.jsonl"
    count = source_transformer.write_to_file(str(output_file))

    lines = output_file.read_text().splitlines()
    assert count == len(lines) == source_transformer.transformed_record_count == 3  # noqa: PLR2004
    assert len(source_transformer.deleted_records) == 1
    assert all(json.loads(line)["timdex_record_id"] for line in lines)


def test_transformer_load_reads_source_records_as_bytes(source_input_file):
    transformer = Transformer.load("cool-repo", source_input_file)
    assert isinstance(next(transformer.source_records), bytes)


def test_transformer_next_iter_parses_bytes_source_record(source_input_file):
    transformer = Transformer.load("cool-repo", source_input_file)
    with mock.patch.object(
        transformer, "parse_source_record", wraps=transformer.parse_source_record
    ) as mocked_parse:
        dataset_record = next(transformer)
    mocked_parse.assert_called_once()
    assert isinstance(mocked_parse.call_args.args[0], bytes)
    assert dataset_record.action == "index"


def test_transformer_next_iter_unparseable_source_record_sets_action_error():
    transformer = MITAardvark("gismit", iter([b"not json"]))
    dataset_record = next(transformer)
    assert dataset_record.action == "error"
    assert dataset_record.source_record == b"not json"
    assert transformer.error_record_count == 1


def test_xmltransformer_read_source_file_yields_record_bytes():
    records = list(XMLTransformer.read_source_file("tests/fixtures/oai_pmh_records.xml"))
    assert all(isinstance(record, bytes) for record in records)
    assert XMLTransformer.parse_source_record(records[0]).find("record")


def test_jsontransformer_read_source_file_yields_line_bytes(tmp_path):
    source_file = tmp_path / "records.jsonl"
    source_file.write_text('{"id": "1"}\n\n{"id": "2"}\r\n')
    assert list(JSONTransformer.read_source_file(str(source_file))) == [
        b'{"id": "1"}',
        b'{"id": "2"}',
    ]


def test_transformer_next_iter_stores_original_source_record_bytes(source_input_file):
    original_records = list(XMLTransformer.read_source_file(source_input_file))
    transformer = Transformer.load("cool-repo", source_input_file)
    stored_records = [dataset_record.source_record for dataset_record in transformer]
    assert stored_records == original_records
    assert not stored_records[0].startswith(b"<?xml")


def test_transformer_next_iter_stores_original_json_line(tmp_path):
    source_file = tmp_path / "gismit-2024-01-01-full-extracted-records-to-index.jsonl"
    line = (
        Path("tests/fixtures/aardvark/aardvark_record_all_fields.jsonl")
        .read_bytes()
        .strip()
    )
    source_file.write_bytes(line + b"\n")
    transformer = Transformer.load("gismit", str(source_file))
    assert next(transformer).source_record == line


def test_transformer_serialize_source_record_lxml_element(generic_transformer):
    element = etree.fromstring(b'<record><title lang="en">Title</title></record>')
    assert (
        generic_transformer("cool-repo", iter([])).serialize_source_record(element)
        == b'<record><title lang="en">Title</title></record>'
    )
