import transmogrifier.models as timdex
from transmogrifier.helpers import parse_xml_records
from transmogrifier.sources.springshare import SpringshareOaiDc

FIXTURES_PREFIX = "tests/fixtures/oai_dc/springshare/libguides"

BLANK_OR_MISSING_OPTIONAL_FIELDS_TIMDEX = timdex.TimdexRecord(
    source="LibGuides",
    source_link="https://libguides.mit.edu/materials",
    timdex_record_id="libguides:materials",
    title="Materials Science & Engineering",
    citation="Materials Science & Engineering. libguides. "
    "https://libguides.mit.edu/materials",
    content_type=["libguides"],
    format="electronic resource",
    identifiers=[
        timdex.Identifier(value="oai:libguides.com:guides/175846", kind="OAI-PMH")
    ],
    links=[
        timdex.Link(
            url="https://libguides.mit.edu/materials",
            kind="LibGuide URL",
            text="LibGuide URL",
        )
    ],
)


def test_libguide_transform_with_all_fields_transforms_correctly():
    input_records = parse_xml_records(
        f"{FIXTURES_PREFIX}/libguides_record_all_fields.xml"
    )
    output_records = SpringshareOaiDc("libguides", input_records)
    assert next(output_records) == timdex.TimdexRecord(
        source="LibGuides",
        source_link="https://libguides.mit.edu/materials",
        timdex_record_id="libguides:materials",
        title="Materials Science & Engineering",
        citation="Ye Li. Materials Science & Engineering. MIT Libraries. libguides. "
        "https://libguides.mit.edu/materials",
        content_type=["libguides"],
        contributors=[
            timdex.Contributor(
                value="Ye Li",
                kind="Creator",
            )
        ],
        dates=[
            timdex.Date(value="2008-06-19T17:55:27"),
        ],
        format="electronic resource",
        identifiers=[
            timdex.Identifier(value="oai:libguides.com:guides/175846", kind="OAI-PMH")
        ],
        links=[
            timdex.Link(
                url="https://libguides.mit.edu/materials",
                kind="LibGuide URL",
                text="LibGuide URL",
            )
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


def test_libguides_transform_with_optional_fields_blank_transforms_correctly():
    input_records = parse_xml_records(
        f"{FIXTURES_PREFIX}/libguides_record_optional_fields_blank.xml"
    )
    output_records = SpringshareOaiDc("libguides", input_records)
    assert next(output_records) == BLANK_OR_MISSING_OPTIONAL_FIELDS_TIMDEX


def test_libguides_transform_with_optional_fields_missing_transforms_correctly():
    input_records = parse_xml_records(
        f"{FIXTURES_PREFIX}/libguides_record_optional_fields_missing.xml"
    )
    output_records = SpringshareOaiDc("libguides", input_records)
    assert next(output_records) == BLANK_OR_MISSING_OPTIONAL_FIELDS_TIMDEX
