from pytest import raises

from transmogrifier.helpers import parse_xml_records


def test_read_xml_records_returns_record_iterator():
    records = parse_xml_records("tests/fixtures/datacite/jpal_records.xml")
    assert len(list(records)) == 38


def test_read_records_raises_error():
    records = parse_xml_records("tests/fixtures/no_records.xml")
    with raises(ValueError):
        next(records)


# TODO: add read from S3 with moto

# TODO: add tests for write function, including to S3 with moto
