import logging
from datetime import datetime

import transmogrifier.models as timdex
from transmogrifier.helpers import (
    generate_citation,
    load_exclusion_list,
    parse_date_from_string,
    validate_date,
    validate_date_range,
)


def test_generate_citation_with_required_fields_only(timdex_record_required_fields):
    assert (
        generate_citation(timdex_record_required_fields)
        == "Some Data About Trees. https://example.com/123"
    )


def test_generate_citation_includes_only_expected_contributors(
    timdex_record_required_fields,
):
    timdex_record_required_fields.contributors = [
        timdex.Contributor(value="Contributor with no kind"),
        timdex.Contributor(value="Contributor with excluded kind", kind="Illustrator"),
        timdex.Contributor(value="Contributor One", kind="Author"),
        timdex.Contributor(value="Contributor Two", kind="Creator"),
    ]
    assert (
        generate_citation(timdex_record_required_fields)
        == "Contributor One, Contributor Two. Some Data About Trees. "
        "https://example.com/123"
    )


def test_generate_citation_includes_only_publication_date(timdex_record_required_fields):
    timdex_record_required_fields.dates = [
        timdex.Date(value="Date with no kind"),
        timdex.Date(value="Not a publication date", kind="Collection date"),
        timdex.Date(value="2022-01-01", kind="Publication date"),
    ]
    assert (
        generate_citation(timdex_record_required_fields)
        == "Some Data About Trees. 2022-01-01. https://example.com/123"
    )


def test_generate_citation_handles_publication_date_with_no_value(
    timdex_record_required_fields,
):
    timdex_record_required_fields.dates = [timdex.Date(kind="Publication date")]
    assert (
        generate_citation(timdex_record_required_fields)
        == "Some Data About Trees. https://example.com/123"
    )


def test_generate_citation_with_creator_and_publication_date(
    timdex_record_required_fields,
):
    timdex_record_required_fields.contributors = [
        timdex.Contributor(kind="author", value="Smith, Susie Q.")
    ]
    timdex_record_required_fields.dates = [
        timdex.Date(kind="Publication date", value="2022")
    ]
    assert (
        generate_citation(timdex_record_required_fields)
        == "Smith, Susie Q. (2022): Some Data About Trees. https://example.com/123"
    )


def test_generate_citation_with_creator_no_publication_date(
    timdex_record_required_fields,
):
    timdex_record_required_fields.contributors = [
        timdex.Contributor(kind="author", value="Smith, Susie Q.")
    ]
    assert (
        generate_citation(timdex_record_required_fields)
        == "Smith, Susie Q. Some Data About Trees. https://example.com/123"
    )


def test_generate_citation_with_publication_date_no_creator(
    timdex_record_required_fields,
):
    timdex_record_required_fields.dates = [
        timdex.Date(kind="Publication date", value="2022")
    ]
    assert (
        generate_citation(timdex_record_required_fields)
        == "Some Data About Trees. 2022. https://example.com/123"
    )


def test_generate_citation_with_no_publisher(timdex_record_required_fields):
    timdex_record_required_fields.content_type = ["Article"]
    timdex_record_required_fields.contributors = [
        timdex.Contributor(kind="author", value="Smith, Susie Q.")
    ]
    timdex_record_required_fields.dates = [
        timdex.Date(kind="Publication date", value="2022")
    ]
    assert (
        generate_citation(timdex_record_required_fields)
        == "Smith, Susie Q. (2022): Some Data About Trees. Article. "
        "https://example.com/123"
    )


def test_generate_citation_includes_only_first_publisher(timdex_record_required_fields):
    timdex_record_required_fields.contributors = [
        timdex.Contributor(kind="author", value="Smith, Susie Q.")
    ]
    timdex_record_required_fields.dates = [
        timdex.Date(kind="Publication date", value="2022")
    ]
    timdex_record_required_fields.publishers = [
        timdex.Publisher(name="Massachusetts Institute of Technology"),
        timdex.Publisher(name="Additional publication information"),
    ]
    assert (
        generate_citation(timdex_record_required_fields)
        == "Smith, Susie Q. (2022): Some Data About Trees. Massachusetts Institute of "
        "Technology. https://example.com/123"
    )


def test_generate_citation_with_no_resource_type(timdex_record_required_fields):
    timdex_record_required_fields.contributors = [
        timdex.Contributor(kind="author", value="Smith, Susie Q.")
    ]
    timdex_record_required_fields.dates = [
        timdex.Date(kind="Publication date", value="2022")
    ]
    timdex_record_required_fields.publishers = [
        timdex.Publisher(name="Massachusetts Institute of Technology")
    ]
    assert (
        generate_citation(timdex_record_required_fields)
        == "Smith, Susie Q. (2022): Some Data About Trees. Massachusetts Institute of "
        "Technology. https://example.com/123"
    )


def test_generate_citation_includes_all_resource_types(timdex_record_required_fields):
    timdex_record_required_fields.content_type = ["Article", "Paper"]
    timdex_record_required_fields.contributors = [
        timdex.Contributor(kind="author", value="Smith, Susie Q.")
    ]
    timdex_record_required_fields.dates = [
        timdex.Date(kind="Publication date", value="2022")
    ]
    timdex_record_required_fields.publishers = [
        timdex.Publisher(name="Massachusetts Institute of Technology")
    ]
    assert (
        generate_citation(timdex_record_required_fields)
        == "Smith, Susie Q. (2022): Some Data About Trees. Massachusetts Institute of "
        "Technology. Article, Paper. https://example.com/123"
    )


def test_generate_citation_with_all_fields(timdex_record_required_fields):
    timdex_record_required_fields.content_type = ["Article"]
    timdex_record_required_fields.contributors = [
        timdex.Contributor(kind="author", value="Smith, Susie Q."),
        timdex.Contributor(kind="creator", value="Jones, John J."),
    ]
    timdex_record_required_fields.dates = [
        timdex.Date(kind="Publication date", value="2022")
    ]
    timdex_record_required_fields.publishers = [
        timdex.Publisher(name="Massachusetts Institute of Technology")
    ]
    assert (
        generate_citation(timdex_record_required_fields)
        == "Smith, Susie Q., Jones, John J. (2022): Some Data About Trees. "
        "Massachusetts Institute of Technology. Article. https://example.com/123"
    )


def test_load_exclusion_list(mock_s3):
    assert load_exclusion_list(
        "s3://test-bucket/libguides/config/libguides-exclusions.csv"
    ) == [
        "https://libguides.mit.edu/excluded1",
        "https://libguides.mit.edu/excluded2",
    ]


def test_parse_date_from_string_success():
    for date in [
        "1930",
        "1930-12",
        "30-12",
        "30-12-31",
        "1930-12-31",
        "301231",
        "19301231",
        "12/31/30",
        "12/31/1930",
        "1930/12/31",
        "30T12",
        "30T12Z",
        "30T12:34",
        "30T12:34Z",
        "30T12:34:56",
        "30T12:34:56Z",
        "30T12:34:56.000001",
        "30T12:34:56.000001Z",
        "30-12T12",
        "30-12T12Z",
        "30-12T12:34",
        "30-12T12:34Z",
        "30-12T12:34:56",
        "30-12T12:34:56Z",
        "30-12T12:34:56.000001",
        "30-12T12:34:56.000001Z",
        "30-12-31T12",
        "30-12-31T12Z",
        "30-12-31T12:34",
        "30-12-31T12:34Z",
        "30-12-31T12:34:56",
        "30-12-31T12:34:56Z",
        "30-12-31T12:34:56.000001",
        "30-12-31T12:34:56.000001Z",
        "1930T12",
        "1930T12Z",
        "1930T12:34",
        "1930T12:34Z",
        "1930T12:34:56",
        "1930T12:34:56Z",
        "1930T12:34:56.000001",
        "1930T12:34:56.000001Z",
        "1930-12T12",
        "1930-12T12Z",
        "1930-12T12:34",
        "1930-12T12:34Z",
        "1930-12T12:34:56",
        "1930-12T12:34:56Z",
        "1930-12T12:34:56.000001",
        "1930-12T12:34:56.000001Z",
        "1930-12-31T12",
        "1930-12-31T12Z",
        "1930-12-31T12:34",
        "1930-12-31T12:34Z",
        "1930-12-31T12:34:56",
        "1930-12-31T12:34:56Z",
        "1930-12-31T12:34:56.000001",
        "1930-12-31T12:34:56.000001Z",
    ]:
        assert isinstance(parse_date_from_string(date), datetime)


def test_parse_date_from_string_invalid_date_returns_none():
    assert parse_date_from_string("circa 1930s") is None


def test_validate_date_success():
    assert validate_date("1930", "1234") is True


def test_validate_date_invalid_date_logs_error(caplog):
    caplog.set_level(logging.DEBUG)
    assert validate_date("circa 1930s", "1234") is False
    assert (
        "Record ID '1234' has a date that couldn't be parsed: 'circa 1930s'"
    ) in caplog.text


def test_validate_date_whitespace_date_logs_error(caplog):
    caplog.set_level(logging.DEBUG)
    assert validate_date("1930  ", "1234") is False
    assert (
        "Record ID '1234' has a date that couldn't be parsed: '1930  '"
    ) in caplog.text


def test_validate_date_range_success():
    assert validate_date_range("1926", "1930", "1234") is True


def test_validate_date_range_invalid_date_range_logs_error(caplog):
    caplog.set_level(logging.DEBUG)
    assert validate_date_range("circa 1910s", "1924", "1234") is False
    assert (
        "Record ID '1234' has invalid values in a date range: 'circa 1910s', '1924'"
    ) in caplog.text


def test_validate_date_range_invalid_start_date_logs_error(caplog):
    caplog.set_level(logging.DEBUG)
    assert validate_date_range("1930", "1924", "1234") is False
    assert (
        "Record ID '1234' has a later start date than end date: '1930', '1924'"
    ) in caplog.text
