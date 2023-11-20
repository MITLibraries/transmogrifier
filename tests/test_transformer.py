from unittest.mock import patch

from transmogrifier.helpers import parse_xml_records
from transmogrifier.models import TimdexRecord
from transmogrifier.sources.datacite import Datacite
from transmogrifier.sources.transformer import Transformer, XmlTransformer


def test_transformer_initializes_with_expected_attributes(oai_pmh_records):
    transformer = Transformer("cool-repo", oai_pmh_records)
    assert transformer.source == "cool-repo"
    assert transformer.source_base_url == "https://example.com/"
    assert transformer.source_name == "A Cool Repository"
    assert transformer.source_records == oai_pmh_records


def test_xmltransformer_initializes_with_expected_attributes(oai_pmh_records):
    transformer = XmlTransformer("cool-repo", oai_pmh_records)
    assert transformer.source == "cool-repo"
    assert transformer.source_base_url == "https://example.com/"
    assert transformer.source_name == "A Cool Repository"
    assert transformer.source_records == oai_pmh_records


def test_xmltransformer_iterates_through_all_records(oai_pmh_records):
    output_records = XmlTransformer("cool-repo", oai_pmh_records)
    assert len(list(output_records)) == 2
    assert output_records.processed_record_count == 3
    assert output_records.transformed_record_count == 2
    assert len(output_records.deleted_records) == 1


def test_xmltransformer_iterates_successfully_if_get_optional_fields_returns_none(
    oai_pmh_records,
):
    with patch(
        "transmogrifier.sources.transformer.XmlTransformer.get_optional_fields"
    ) as m:
        m.return_value = None
        output_records = XmlTransformer("cool-repo", oai_pmh_records)
        assert len(list(output_records)) == 0
        assert output_records.processed_record_count == 3
        assert output_records.skipped_record_count == 2
        assert output_records.transformed_record_count == 0
        assert len(output_records.deleted_records) == 1


def test_xmltransformer_parse_source_file_returns_record_iterator():
    records = XmlTransformer.parse_source_file(
        "tests/fixtures/datacite/datacite_records.xml"
    )
    assert len(list(records)) == 38


def test_xmltransformer_record_is_deleted_returns_true_if_deleted(caplog):
    source_records = parse_xml_records("tests/fixtures/record_deleted.xml")
    assert XmlTransformer.record_is_deleted(next(source_records)) is True


def test_xmltransformer_get_required_fields_returns_expected_values(oai_pmh_records):
    transformer = XmlTransformer("cool-repo", oai_pmh_records)
    assert transformer.get_required_fields(next(oai_pmh_records)) == {
        "source": "A Cool Repository",
        "source_link": "https://example.com/12345",
        "timdex_record_id": "cool-repo:12345",
        "title": "Title not provided",
    }


def test_xmltransformer_transform_returns_timdex_record(oai_pmh_records):
    transformer = XmlTransformer("cool-repo", oai_pmh_records)
    assert next(transformer) == TimdexRecord(
        source="A Cool Repository",
        source_link="https://example.com/12345",
        timdex_record_id="cool-repo:12345",
        title="Title not provided",
        citation="Title not provided. https://example.com/12345",
        content_type=["Not specified"],
    )


def test_xmltransformer_get_valid_title_with_title_field_blank_logs_warning(caplog):
    source_records = parse_xml_records("tests/fixtures/record_title_field_blank.xml")
    output_records = Datacite("cool-repo", source_records)
    assert next(output_records).title == "Title not provided"
    assert (
        "Record doi:10.7910/DVN/19PPE7 was missing a title, source record should be "
        "investigated." in caplog.text
    )


def test_xmltransformer_get_valid_title_with_title_field_missing_logs_warning(caplog):
    source_records = parse_xml_records("tests/fixtures/record_title_field_missing.xml")
    output_records = Datacite("cool-repo", source_records)
    assert next(output_records).title == "Title not provided"
    assert (
        "Record doi:10.7910/DVN/19PPE7 was missing a title, source record should be "
        "investigated." in caplog.text
    )


def test_xmltransformer_get_valid_title_with_title_field_multiple_logs_warning(caplog):
    source_records = parse_xml_records("tests/fixtures/record_title_field_multiple.xml")
    output_records = Datacite("cool-repo", source_records)
    assert (
        next(output_records).title
        == "The Impact of Maternal Literacy and Participation Programs"
    )
    assert (
        "Record doi:10.7910/DVN/19PPE7 has multiple titles. Using the first title from "
        "the following titles found: [<title>The Impact of Maternal Literacy and "
        "Participation Programs</title>, <title>Additional Title</title>]"
        in caplog.text
    )
