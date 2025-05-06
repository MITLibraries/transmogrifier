# ruff: noqa: PLR2004

import transmogrifier.models as timdex
from transmogrifier.sources.xml.datacite import Datacite
from transmogrifier.sources.xmltransformer import XMLTransformer


def test_xmltransformer_initializes_with_expected_attributes(oai_pmh_records):
    transformer = XMLTransformer("cool-repo", oai_pmh_records)
    assert transformer.source == "cool-repo"
    assert transformer.source_base_url == "https://example.com/"
    assert transformer.source_name == "A Cool Repository"
    assert transformer.source_records == oai_pmh_records


def test_xmltransformer_iterates_through_all_records(caplog, oai_pmh_records):
    caplog.set_level("DEBUG")
    output_records = XMLTransformer("cool-repo", oai_pmh_records)
    assert len(list(output_records)) == 3
    assert output_records.processed_record_count == 3
    assert output_records.transformed_record_count == 2
    assert len(output_records.deleted_records) == 1


def test_xmltransformer_parse_source_file_returns_record_iterator():
    records = XMLTransformer.parse_source_file(
        "tests/fixtures/datacite/datacite_records.xml"
    )
    assert len(list(records)) == 38


def test_xmltransformer_record_is_deleted_returns_true_if_deleted(caplog):
    source_records = XMLTransformer.parse_source_file("tests/fixtures/record_deleted.xml")
    assert XMLTransformer.record_is_deleted(next(source_records)) is True


def test_xmltransformer_record_is_deleted_returns_false_if_not_deleted(caplog):
    source_records = XMLTransformer.parse_source_file(
        "tests/fixtures/record_title_field_blank.xml"
    )
    assert XMLTransformer.record_is_deleted(next(source_records)) is False


def test_xmltransformer_transform_returns_timdex_record(oai_pmh_records):
    transformer = XMLTransformer("cool-repo", oai_pmh_records)
    timdex_record = transformer.transform(next(transformer.source_records))
    assert timdex_record == timdex.TimdexRecord(
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
    timdex_record = output_records.transform(next(output_records.source_records))
    assert timdex_record.title == "Title not provided"
    assert (
        "Record doi:10.7910/DVN/19PPE7 was missing a title, source record should be "
        "investigated." in caplog.text
    )


def test_xmltransformer_get_valid_title_with_title_field_missing_logs_warning(caplog):
    source_records = XMLTransformer.parse_source_file(
        "tests/fixtures/record_title_field_missing.xml"
    )
    output_records = Datacite("cool-repo", source_records)
    timdex_record = output_records.transform(next(output_records.source_records))
    assert timdex_record.title == "Title not provided"
    assert (
        "Record doi:10.7910/DVN/19PPE7 was missing a title, source record should be "
        "investigated." in caplog.text
    )


def test_xmltransformer_get_valid_title_with_title_field_multiple_logs_warning(caplog):
    source_records = XMLTransformer.parse_source_file(
        "tests/fixtures/record_title_field_multiple.xml"
    )
    output_records = Datacite("cool-repo", source_records)
    timdex_record = output_records.transform(next(output_records.source_records))
    assert (
        timdex_record.title
        == "The Impact of Maternal Literacy and Participation Programs"
    )
    assert (
        "Record doi:10.7910/DVN/19PPE7 has multiple titles. Using the first title from "
        "the following titles found: ['The Impact of Maternal Literacy and "
        "Participation Programs', 'Additional Title']" in caplog.text
    )
