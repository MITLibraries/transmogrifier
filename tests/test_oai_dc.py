import logging

import transmogrifier.models as timdex
from transmogrifier.helpers import parse_xml_records
from transmogrifier.sources.oaidc import OaiDc

FIXTURES_PREFIX = "tests/fixtures/oai_dc"

BLANK_OR_MISSING_OPTIONAL_FIELDS_TIMDEX = timdex.TimdexRecord(
    source="Libguides",
    source_link="https://libguides.mit.edu/guides/175846",
    timdex_record_id="libguides:guides-175846",
    title="Materials Science & Engineering",
    citation="Materials Science & Engineering. Libguides. "
    "https://libguides.mit.edu/materials",
    content_type=["libguides"],
    format="electronic resource",
    identifiers=[
        timdex.Identifier(value="oai:libguides.com:guides/175846", kind="OAI-PMH")
    ],
)


def test_oaidctransform_with_all_fields_transforms_correctly():
    input_records = parse_xml_records(f"{FIXTURES_PREFIX}/oaidc_record_all_fields.xml")
    output_records = OaiDc("libguides", input_records)
    assert next(output_records) == timdex.TimdexRecord(
        source="Libguides",
        source_link="https://libguides.mit.edu/guides/175846",
        timdex_record_id="libguides:guides-175846",
        title="Materials Science & Engineering",
        citation="Materials Science & Engineering. Libguides. "
        "https://libguides.mit.edu/materials",
        content_type=["libguides"],
        contributors=[
            timdex.Contributor(
                value="Ye Li",
                kind="Creator",
            )
        ],
        format="electronic resource",
        identifiers=[
            timdex.Identifier(value="oai:libguides.com:guides/175846", kind="OAI-PMH")
        ],
        publication_information=["MIT Libraries"],
        subjects=[
            timdex.Subject(
                value=["Engineering", "Science"],
                kind="Subject scheme not provided",
            ),
        ],
        summary=["Useful databases and other research tips for materials science."],
    )


def test_oaidc_transform_with_optional_fields_blank_transforms_correctly():
    input_records = parse_xml_records(
        f"{FIXTURES_PREFIX}/oaidc_record_optional_fields_blank.xml"
    )
    output_records = OaiDc("libguides", input_records)
    assert next(output_records) == BLANK_OR_MISSING_OPTIONAL_FIELDS_TIMDEX


def test_oaidc_transform_with_optional_fields_missing_transforms_correctly():
    input_records = parse_xml_records(
        f"{FIXTURES_PREFIX}/oaidc_record_optional_fields_missing.xml"
    )
    output_records = OaiDc("libguides", input_records)
    assert next(output_records) == BLANK_OR_MISSING_OPTIONAL_FIELDS_TIMDEX


def test_oaidc_generic_date():
    """
    Test generic get_dates() definition returns a validated timdex.Date
    """

    input_records = parse_xml_records(
        f"{FIXTURES_PREFIX}/oaidc_record_valid_generic_date.xml"
    )
    transformer_instance = OaiDc("libguides", input_records)
    xml = next(transformer_instance.input_records)
    assert transformer_instance.get_dates(xml) == [
        timdex.Date(kind=None, note=None, range=None, value="2008-06-19T17:55:27")
    ]


def test_oaidc_missing_required_fields(caplog):
    input_records = parse_xml_records(
        f"{FIXTURES_PREFIX}/oaidc_record_missing_required_fields.xml"
    )
    output_records = OaiDc("libguides", input_records)
    assert len(list(output_records)) == 0
    assert output_records.processed_record_count == 1
    assert (
        "transmogrifier.sources.oaidc",
        logging.ERROR,
        "dc:title or dc:identifier is missing or blank",
    ) in caplog.record_tuples
