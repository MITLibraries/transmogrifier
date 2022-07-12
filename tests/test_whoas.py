from transmogrifier.helpers import parse_xml_records
from transmogrifier.sources.whoas import WHOAS


def test_whoas_get_content_type_returns_accepted_content_type():
    input_records = parse_xml_records(
        "tests/fixtures/dspace/dspace_dim_record_all_fields.xml"
    )
    output_records = WHOAS("whoas", input_records)
    whoas_record = next(output_records)
    assert whoas_record.content_type == ["Moving Image"]


def test_whoas_get_content_type_filters_unaccepted_content_type():
    input_records = parse_xml_records(
        "tests/fixtures/dspace/whoas_record_unaccepted_content_types.xml"
    )
    output_records = WHOAS("whoas", input_records)
    assert next(output_records) is None
