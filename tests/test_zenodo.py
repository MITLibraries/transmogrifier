from transmogrifier.helpers import parse_xml_records
from transmogrifier.sources.zenodo import Zenodo


def test_zenodo_create_source_record_id_generates_correct_id():
    input_records = parse_xml_records("tests/fixtures/datacite/zenodo_record.xml")
    output_records = Zenodo("zenodo", input_records)
    zenodo_record = next(output_records)
    assert zenodo_record.source_link == "https://zenodo.org/record/4291646"
    assert zenodo_record.timdex_record_id == "zenodo:4291646"


def test_zenodo_validate_content_types_returns_accepted_content_type():
    input_records = parse_xml_records("tests/fixtures/datacite/zenodo_record.xml")
    output_records = Zenodo("zenodo", input_records)
    zenodo_record = next(output_records)
    assert zenodo_record.content_type == ["Software"]


def test_zenodo_validate_content_types_filters_unaccepted_content_types():
    input_records = list(
        parse_xml_records(
            "tests/fixtures/datacite/zenodo_records_"
            "containing_unaccepted_content_types.xml"
        )
    )
    assert len(input_records) == 2
    output_records = Zenodo("zenodo", iter(input_records))
    assert len(list(output_records)) == 1
