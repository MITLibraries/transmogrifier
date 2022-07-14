import transmogrifier.models as timdex
from transmogrifier.helpers import parse_xml_records
from transmogrifier.sources.whoas import WHOAS


def test_whoas_get_content_type_returns_accepted_content_type():
    input_records = parse_xml_records(
        "tests/fixtures/dspace/dspace_dim_record_all_fields.xml"
    )
    output_records = WHOAS("whoas", input_records)
    whoas_record = next(output_records)
    assert whoas_record.content_type == ["Moving Image"]


def test_whoas_get_content_type_filters_unaccepted_content_types():
    input_records = parse_xml_records(
        "tests/fixtures/dspace/whoas_records_containing_unaccepted_content_types.xml"
    )
    output_records = WHOAS("whoas", input_records)
    assert next(output_records) == timdex.TimdexRecord(
        source="Woods Hole Open Access Server",
        source_link="https://darchive.mblwhoilibrary.org/handle/1912/2641",
        timdex_record_id="whoas:1912-2641",
        title="Time lapse movie of meiosis I",
        citation=(
            "Time lapse movie of meiosis I. Moving Image. "
            "https://darchive.mblwhoilibrary.org/handle/1912/2641"
        ),
        content_type=["Moving Image"],
        format="electronic resource",
    )
