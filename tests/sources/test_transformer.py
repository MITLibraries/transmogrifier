# ruff: noqa: PLR2004
from pathlib import Path
from unittest.mock import patch

import pytest

import transmogrifier.models as timdex
from transmogrifier.sources.transformer import Transformer, XMLTransformer
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


def test_create_dates_and_locations_from_publishers_success():
    fields = {
        "publishers": [
            timdex.Publisher(name="Publisher", date="Date", location="Location")
        ],
    }
    assert Transformer.create_dates_and_locations_from_publishers(fields) == {
        "publishers": [
            timdex.Publisher(name="Publisher", date="Date", location="Location")
        ],
        "dates": [timdex.Date(kind="Publication date", value="Date")],
        "locations": [timdex.Location(value="Location", kind="Publisher")],
    }


def test_xmltransformer_initializes_with_expected_attributes(oai_pmh_records):
    transformer = XMLTransformer("cool-repo", oai_pmh_records)
    assert transformer.source == "cool-repo"
    assert transformer.source_base_url == "https://example.com/"
    assert transformer.source_name == "A Cool Repository"
    assert transformer.source_records == oai_pmh_records


def test_xmltransformer_iterates_through_all_records(oai_pmh_records):
    output_records = XMLTransformer("cool-repo", oai_pmh_records)
    assert len(list(output_records)) == 2
    assert output_records.processed_record_count == 3
    assert output_records.transformed_record_count == 2
    assert len(output_records.deleted_records) == 1


def test_xmltransformer_iterates_successfully_if_get_optional_fields_returns_none(
    oai_pmh_records,
):
    with patch(
        "transmogrifier.sources.transformer.XMLTransformer.get_optional_fields"
    ) as m:
        m.return_value = None
        output_records = XMLTransformer("cool-repo", oai_pmh_records)
        assert len(list(output_records)) == 0
        assert output_records.processed_record_count == 3
        assert output_records.skipped_record_count == 2
        assert output_records.transformed_record_count == 0
        assert len(output_records.deleted_records) == 1


def test_xmltransformer_transform_and_write_output_files_writes_output_files(
    tmp_path, oai_pmh_records
):
    output_file = str(tmp_path / "output_file.json")
    transformer = XMLTransformer("cool-repo", oai_pmh_records)
    assert not Path(tmp_path / "output_file.json").exists()
    assert not Path(tmp_path / "output_file.txt").exists()
    transformer.transform_and_write_output_files(output_file)
    assert Path(tmp_path / "output_file.json").exists()
    assert Path(tmp_path / "output_file.txt").exists()


def test_xmltransformer_transform_and_write_output_files_no_txt_file_if_not_needed(
    tmp_path,
):
    output_file = str(tmp_path / "output_file.json")
    datacite_records = XMLTransformer.parse_source_file(
        "tests/fixtures/datacite/datacite_records.xml"
    )
    transformer = XMLTransformer("cool-repo", datacite_records)
    transformer.transform_and_write_output_files(output_file)
    assert len(list(tmp_path.iterdir())) == 1
    assert next(tmp_path.iterdir()).name == "output_file.json"


def test_xmltransformer_parse_source_file_returns_record_iterator():
    records = XMLTransformer.parse_source_file(
        "tests/fixtures/datacite/datacite_records.xml"
    )
    assert len(list(records)) == 38


def test_xmltransformer_record_is_deleted_returns_true_if_deleted(caplog):
    source_records = XMLTransformer.parse_source_file("tests/fixtures/record_deleted.xml")
    assert XMLTransformer.record_is_deleted(next(source_records)) is True


def test_xmltransformer_get_required_fields_returns_expected_values(oai_pmh_records):
    transformer = XMLTransformer("cool-repo", oai_pmh_records)
    assert transformer.get_required_fields(next(oai_pmh_records)) == {
        "source": "A Cool Repository",
        "source_link": "https://example.com/12345",
        "timdex_record_id": "cool-repo:12345",
        "title": "Title not provided",
    }


def test_xmltransformer_transform_returns_timdex_record(oai_pmh_records):
    transformer = XMLTransformer("cool-repo", oai_pmh_records)
    assert next(transformer) == timdex.TimdexRecord(
        source="A Cool Repository",
        source_link="https://example.com/12345",
        timdex_record_id="cool-repo:12345",
        title="Title not provided",
        citation="Title not provided. https://example.com/12345",
        content_type=["Not specified"],
    )


def test_xmltransformer_get_valid_title_with_title_field_blank_logs_warning(caplog):
    source_records = XMLTransformer.parse_source_file(
        "tests/fixtures/record_title_field_blank.xml"
    )
    output_records = Datacite("cool-repo", source_records)
    assert next(output_records).title == "Title not provided"
    assert (
        "Record doi:10.7910/DVN/19PPE7 was missing a title, source record should be "
        "investigated." in caplog.text
    )


def test_xmltransformer_get_valid_title_with_title_field_missing_logs_warning(caplog):
    source_records = XMLTransformer.parse_source_file(
        "tests/fixtures/record_title_field_missing.xml"
    )
    output_records = Datacite("cool-repo", source_records)
    assert next(output_records).title == "Title not provided"
    assert (
        "Record doi:10.7910/DVN/19PPE7 was missing a title, source record should be "
        "investigated." in caplog.text
    )


def test_xmltransformer_get_valid_title_with_title_field_multiple_logs_warning(caplog):
    source_records = XMLTransformer.parse_source_file(
        "tests/fixtures/record_title_field_multiple.xml"
    )
    output_records = Datacite("cool-repo", source_records)
    assert (
        next(output_records).title
        == "The Impact of Maternal Literacy and Participation Programs"
    )
    assert (
        "Record doi:10.7910/DVN/19PPE7 has multiple titles. Using the first title from "
        "the following titles found: ['The Impact of Maternal Literacy and "
        "Participation Programs', 'Additional Title']" in caplog.text
    )
