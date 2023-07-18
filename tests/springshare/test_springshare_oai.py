import logging

from transmogrifier.helpers import parse_xml_records
from transmogrifier.sources.springshare.libguides import Libguides


def test_springshare_oai_missing_or_blank_required_elements(caplog):
    """
    Test that record is skipped and logs ALL missing required elements
    """
    input_records = parse_xml_records(
        "tests/fixtures/springshare/springshare_oai_missing_or_blank_required_elements"
        ".xml"
    )
    output_records = Libguides("libguides", input_records)
    assert len(list(output_records)) == 0
    assert output_records.processed_record_count == 1
    assert output_records.skipped_record_count == 1
    assert (
        "transmogrifier.sources.springshare",
        logging.ERROR,
        "'dc:identifier' is missing or empty",
    ) in caplog.record_tuples
    assert (
        "transmogrifier.sources.springshare",
        logging.ERROR,
        "'dc:title' is missing or empty",
    ) in caplog.record_tuples
