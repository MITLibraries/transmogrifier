import transmogrifier.models as timdex
from transmogrifier.helpers import parse_xml_records
from transmogrifier.sources.springshare.research_databases import ResearchDatabases

BLANK_OR_MISSING_OPTIONAL_FIELDS_TIMDEX = timdex.TimdexRecord(
    source="Research Databases",
    source_link="https://libguides.mit.edu/llba",
    timdex_record_id="researchdatabases:llba",
    title="Linguistics and Language Behavior Abstracts (LLBA)",
    citation="Linguistics and Language Behavior Abstracts (LLBA). Research "
    "Databases. https://libguides.mit.edu/llba",
    content_type=["researchdatabases"],
    format="electronic resource",
    identifiers=[
        timdex.Identifier(value="oai:libguides.com:az/65257807", kind="OAI-PMH")
    ],
    links=[
        timdex.Link(
            url="https://libguides.mit.edu/llba",
            kind="Research Database URL",
            text="Research Database URL",
        )
    ],
)


def test_libguide_transform_with_all_fields_transforms_correctly():
    input_records = parse_xml_records(
        "tests/fixtures/springshare/research_databases"
        "/research_databases_record_all_fields.xml"
    )
    output_records = ResearchDatabases("researchdatabases", input_records)
    assert next(output_records) == timdex.TimdexRecord(
        source="Research Databases",
        source_link="https://libguides.mit.edu/llba",
        timdex_record_id="researchdatabases:llba",
        title="Linguistics and Language Behavior Abstracts (LLBA)",
        citation="Linguistics and Language Behavior Abstracts (LLBA). Research "
        "Databases. https://libguides.mit.edu/llba",
        content_type=["researchdatabases"],
        dates=[
            timdex.Date(value="2022-01-28T22:15:37"),
        ],
        format="electronic resource",
        identifiers=[
            timdex.Identifier(value="oai:libguides.com:az/65257807", kind="OAI-PMH")
        ],
        links=[
            timdex.Link(
                url="https://libguides.mit.edu/llba",
                kind="Research Database URL",
                text="Research Database URL",
            )
        ],
        subjects=[
            timdex.Subject(
                value=["Humanities"],
                kind="Subject scheme not provided",
            ),
        ],
        summary=[
            "The most comprehensive index to articles in Linguistics and Language\n     "
            "     Development and use."
        ],
    )


def test_research_databases_transform_with_optional_fields_blank_transforms_correctly():
    input_records = parse_xml_records(
        "tests/fixtures/springshare/research_databases"
        "/research_databases_record_optional_fields_blank.xml"
    )
    output_records = ResearchDatabases("researchdatabases", input_records)
    assert next(output_records) == BLANK_OR_MISSING_OPTIONAL_FIELDS_TIMDEX


def test_research_databases_transform_with_optional_fields_missing_transforms_correctly():
    input_records = parse_xml_records(
        "tests/fixtures/springshare/research_databases"
        "/research_databases_record_optional_fields_missing.xml"
    )
    output_records = ResearchDatabases("researchdatabases", input_records)
    assert next(output_records) == BLANK_OR_MISSING_OPTIONAL_FIELDS_TIMDEX
