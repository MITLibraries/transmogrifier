import transmogrifier.models as timdex
from transmogrifier.helpers import parse_xml_records
from transmogrifier.sources.springshare import SpringshareOaiDc

FIXTURES_PREFIX = "tests/fixtures/oai_dc/springshare"


def test_springshare_get_dates_valid():
    """
    Test for valid date parsing
    """

    input_records = parse_xml_records(f"{FIXTURES_PREFIX}/springshare_valid_dates.xml")
    transformer_instance = SpringshareOaiDc("libguides", input_records)

    # asser valid dates
    for xml in transformer_instance.input_records:
        date_field_val = transformer_instance.get_dates("test_get_dates", xml)
        assert date_field_val == [
            timdex.Date(kind=None, note=None, range=None, value="2000-01-01T00:00:00")
        ]


def test_springshare_get_dates_invalid(caplog):
    """
    Tests that bad, missing, or blank data will log and continue to process
    """

    input_records = parse_xml_records(
        f"{FIXTURES_PREFIX}/springshare_invalid_dates.xml"
    )
    transformer_instance = SpringshareOaiDc("libguides", input_records)

    # assert error handling for invalid dates
    for xml in transformer_instance.input_records:
        date_field_val = transformer_instance.get_dates("test_get_dates", xml)
        assert date_field_val is None
        assert "could not parse date for Springshare record" in caplog.text


def test_springshare_get_links_missing_identifier(caplog):
    """
    Tests that links does logs error and continues to process when dc:identifier is absent
    """

    input_records = parse_xml_records(
        f"{FIXTURES_PREFIX}/springshare_record_missing_required_fields.xml"
    )
    transformer_instance = SpringshareOaiDc("libguides", input_records)

    # assert error handling for invalid dates
    for xml in transformer_instance.input_records:
        links_field_val = transformer_instance.get_links("test_get_links", xml)
        assert links_field_val is None
        assert "cannot generate links for Springshare record" in caplog.text
