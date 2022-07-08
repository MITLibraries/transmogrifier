from transmogrifier.helpers import parse_xml_records
from transmogrifier.sources.zenodo import Zenodo


def test_zenodo_create_source_record_id_generates_correct_id():
    input_records = parse_xml_records("tests/fixtures/datacite/zenodo_record.xml")
    output_records = Zenodo("zenodo", input_records)
    zenodo_record = next(output_records)
    assert zenodo_record.source_link == "https://zenodo.org/record/4291646"
    assert zenodo_record.timdex_record_id == "zenodo:4291646"
