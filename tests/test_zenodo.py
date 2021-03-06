from transmogrifier.helpers import parse_xml_records
from transmogrifier.sources.zenodo import Zenodo


def test_zenodo_create_source_record_id_generates_correct_id():
    input_records = parse_xml_records("tests/fixtures/datacite/zenodo_record.xml")
    output_records = Zenodo("zenodo", input_records)
    zenodo_record = next(output_records)
    assert zenodo_record.source_link == "https://zenodo.org/record/4291646"
    assert zenodo_record.timdex_record_id == "zenodo:4291646"


def test_valid_content_types_with_all_invalid():
    content_types = ["journalarticle", "poster"]
    assert Zenodo.valid_content_types(content_types) is False


def test_valid_content_types_with_some_invalid():
    content_types = ["lesson", "dataset"]
    assert Zenodo.valid_content_types(content_types) is True


def test_valid_content_types_with_all_valid():
    content_types = [
        "dataset",
        "diagram",
        "drawing",
        "figure",
        "image",
        "other",
        "photo",
        "physicalobject",
        "plot",
        "software",
        "taxonomictreatment",
        "video",
    ]
    assert Zenodo.valid_content_types(content_types) is True


def test_zenodo_skips_records_with_invalid_content_types():
    input_records = list(
        parse_xml_records(
            "tests/fixtures/datacite/"
            "zenodo_records_with_valid_and_invalid_content_types.xml"
        )
    )
    assert len(input_records) == 2
    output_records = Zenodo("zenodo", iter(input_records))
    assert len(list(output_records)) == 1
