from transmogrifier.helpers import parse_xml_records
from transmogrifier.sources.whoas import Whoas


def test_whoas_validat_content_types_returns_accepted_content_type():
    input_records = parse_xml_records(
        "tests/fixtures/dspace/dspace_dim_record_all_fields.xml"
    )
    output_records = Whoas("whoas", input_records)
    whoas_record = next(output_records)
    assert whoas_record.content_type == ["Moving Image"]


def test_whoas_validate_content_types_filters_unaccepted_content_types():
    input_records = list(
        parse_xml_records(
            "tests/fixtures/dspace/whoas_records_containing_unaccepted_content_types.xml"
        )
    )
    assert len(input_records) == 2
    output_records = Whoas("whoas", iter(input_records))
    assert len(list(output_records)) == 1
