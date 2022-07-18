from unittest.mock import patch

from transmogrifier.helpers import parse_xml_records
from transmogrifier.models import TimdexRecord
from transmogrifier.sources.datacite import Datacite
from transmogrifier.sources.transformer import Transformer


def test_transformer_initializes_with_expected_attributes(oai_pmh_records):
    transformer = Transformer("cool-repo", oai_pmh_records)
    assert transformer.source == "cool-repo"
    assert transformer.source_base_url == "https://example.com/"
    assert transformer.source_name == "A Cool Repository"
    assert transformer.input_records == oai_pmh_records


def test_transformer_iterates_through_all_records(oai_pmh_records):
    output_records = Transformer("cool-repo", oai_pmh_records)
    assert len(list(output_records)) == 2


def test_transformer_iterates_successfully_if_get_optional_fields_returns_none(
    oai_pmh_records,
):
    with patch(
        "transmogrifier.sources.transformer.Transformer.get_optional_fields"
    ) as m:
        m.return_value = None
        output_records = Transformer("cool-repo", oai_pmh_records)
        assert len(list(output_records)) == 0
        assert output_records.processed_record_count == 2
        assert output_records.skipped_record_count == 2
        assert output_records.transformed_record_count == 0


def test_transformer_get_required_fields_returns_expected_values(oai_pmh_records):
    transformer = Transformer("cool-repo", oai_pmh_records)
    assert transformer.get_required_fields(next(oai_pmh_records)) == {
        "source": "A Cool Repository",
        "source_link": "https://example.com/",
        "timdex_record_id": "cool-repo:",
        "title": "Title not provided",
    }


def test_transformer_transform_returns_timdex_record(oai_pmh_records):
    transformer = Transformer("cool-repo", oai_pmh_records)
    assert next(transformer) == TimdexRecord(
        source="A Cool Repository",
        source_link="https://example.com/",
        timdex_record_id="cool-repo:",
        title="Title not provided",
        citation="Title not provided. https://example.com/",
    )


def test_get_valid_title_with_title_field_blank_logs_warning(caplog):
    input_records = parse_xml_records("tests/fixtures/record_title_field_blank.xml")
    output_records = Datacite("cool-repo", input_records)
    assert next(output_records).title == "Title not provided"
    assert (
        "Record doi:10.7910/DVN/19PPE7 was missing a title, source record should be "
        "investigated." in caplog.text
    )


def test_get_valid_title_with_title_field_missing_logs_warning(caplog):
    input_records = parse_xml_records("tests/fixtures/record_title_field_missing.xml")
    output_records = Datacite("cool-repo", input_records)
    assert next(output_records).title == "Title not provided"
    assert (
        "Record doi:10.7910/DVN/19PPE7 was missing a title, source record should be "
        "investigated." in caplog.text
    )


def test_get_valid_title_with_title_field_multiple_logs_warning(caplog):
    input_records = parse_xml_records("tests/fixtures/record_title_field_multiple.xml")
    output_records = Datacite("cool-repo", input_records)
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
