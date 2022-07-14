import transmogrifier.models as timdex
from transmogrifier.helpers import parse_xml_records
from transmogrifier.sources.zenodo import Zenodo


def test_zenodo_create_source_record_id_generates_correct_id():
    input_records = parse_xml_records("tests/fixtures/datacite/zenodo_record.xml")
    output_records = Zenodo("zenodo", input_records)
    zenodo_record = next(output_records)
    assert zenodo_record.source_link == "https://zenodo.org/record/4291646"
    assert zenodo_record.timdex_record_id == "zenodo:4291646"


def test_zenodo_get_content_type_returns_accepted_content_type():
    input_records = parse_xml_records("tests/fixtures/datacite/zenodo_record.xml")
    output_records = Zenodo("zenodo", input_records)
    zenodo_record = next(output_records)
    assert zenodo_record.content_type == ["Software"]


def test_zenodo_get_content_type_filters_unaccepted_content_types():
    input_records = parse_xml_records(
        "tests/fixtures/datacite/zenodo_records_containing_unaccepted_content_types.xml"
    )
    output_records = Zenodo("zenodo", input_records)
    assert next(output_records) == timdex.TimdexRecord(
        source="Zenodo",
        source_link="https://zenodo.org/record/doi:10.7910/DVN/19PPE7",
        timdex_record_id="zenodo:doi:10.7910-DVN-19PPE7",
        title="The Impact of Maternal Literacy and Participation Programs",
        citation=(
            "The Impact of Maternal Literacy and Participation Programs. Dataset. "
            "https://zenodo.org/record/doi:10.7910/DVN/19PPE7"
        ),
        content_type=["Dataset"],
        format="electronic resource",
        identifiers=[timdex.Identifier(value="10.7910/DVN/19PPE7", kind="DOI")],
        links=[
            timdex.Link(
                url="https://zenodo.org/record/doi:10.7910/DVN/19PPE7",
                kind="Digital object URL",
                text="Digital object URL",
            )
        ],
        notes=[timdex.Note(value=["Survey Data"], kind="Datacite resource type")],
    )
