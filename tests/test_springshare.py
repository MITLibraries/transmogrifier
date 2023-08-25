import transmogrifier.models as timdex
from transmogrifier.helpers import parse_xml_records
from transmogrifier.sources.springshare import SpringshareOaiDc

SPRINGSHARE_FIXTURES_PREFIX = "tests/fixtures/oai_dc/springshare"

LIBGUIDES_FIXTURES_PREFIX = f"{SPRINGSHARE_FIXTURES_PREFIX}/libguides"

RESEARCHDATABASES_FIXTURES_PREFIX = f"{SPRINGSHARE_FIXTURES_PREFIX}/research_databases"


LIBGUIDES_BLANK_OR_MISSING_OPTIONAL_FIELDS_TIMDEX = timdex.TimdexRecord(
    source="LibGuides",
    source_link="https://libguides.mit.edu/materials",
    timdex_record_id="libguides:guides-175846",
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

RESEARCHDATABASES_BLANK_OR_MISSING_OPTIONAL_FIELDS_TIMDEX = timdex.TimdexRecord(
    source="Research Databases",
    source_link="https://libguides.mit.edu/llba",
    timdex_record_id="researchdatabases:az-65257807",
    title="Linguistics and Language Behavior Abstracts (LLBA)",
    citation="Linguistics and Language Behavior Abstracts (LLBA). researchdatabases. "
    "https://libguides.mit.edu/llba",
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


def test_springshare_get_dates_valid():
    input_records = parse_xml_records(
        f"{SPRINGSHARE_FIXTURES_PREFIX}/springshare_valid_dates.xml"
    )
    transformer_instance = SpringshareOaiDc("libguides", input_records)
    for xml in transformer_instance.input_records:
        date_field_value = transformer_instance.get_dates("test_get_dates", xml)
        assert date_field_value == [
            timdex.Date(
                kind="Created", note=None, range=None, value="2000-01-01T00:00:00"
            )
        ]


def test_springshare_get_dates_invalid_logged_and_skipped(caplog):
    input_records = parse_xml_records(
        f"{SPRINGSHARE_FIXTURES_PREFIX}/springshare_invalid_dates.xml"
    )
    transformer_instance = SpringshareOaiDc("libguides", input_records)
    for xml in transformer_instance.input_records:
        date_field_value = transformer_instance.get_dates("test_get_dates", xml)
        assert date_field_value is None
        assert "has a date that cannot be parsed" in caplog.text


def test_springshare_get_links_missing_identifier_logged_and_skipped(caplog):
    input_records = parse_xml_records(
        f"{SPRINGSHARE_FIXTURES_PREFIX}/springshare_record_missing_required_fields.xml"
    )
    transformer_instance = SpringshareOaiDc("libguides", input_records)
    for xml in transformer_instance.input_records:
        links_field_value = transformer_instance.get_links("test_get_links", xml)
        assert links_field_value is None
        assert "has links that cannot be generated" in caplog.text


def test_libguide_transform_with_all_fields_transforms_correctly():
    input_records = parse_xml_records(
        f"{LIBGUIDES_FIXTURES_PREFIX}/libguides_record_all_fields.xml"
    )
    output_records = SpringshareOaiDc("libguides", input_records)
    assert next(output_records) == timdex.TimdexRecord(
        source="LibGuides",
        source_link="https://libguides.mit.edu/materials",
        timdex_record_id="libguides:guides-175846",
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
            timdex.Date(value="2008-06-19T17:55:27", kind="Created"),
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
        f"{LIBGUIDES_FIXTURES_PREFIX}/libguides_record_optional_fields_blank.xml"
    )
    output_records = SpringshareOaiDc("libguides", input_records)
    assert next(output_records) == LIBGUIDES_BLANK_OR_MISSING_OPTIONAL_FIELDS_TIMDEX


def test_libguides_transform_with_optional_fields_missing_transforms_correctly():
    input_records = parse_xml_records(
        f"{LIBGUIDES_FIXTURES_PREFIX}/libguides_record_optional_fields_missing.xml"
    )
    output_records = SpringshareOaiDc("libguides", input_records)
    assert next(output_records) == LIBGUIDES_BLANK_OR_MISSING_OPTIONAL_FIELDS_TIMDEX


def test_research_databases_transform_with_all_fields_transforms_correctly():
    input_records = parse_xml_records(
        f"{RESEARCHDATABASES_FIXTURES_PREFIX}/research_databases_record_all_fields.xml"
    )
    output_records = SpringshareOaiDc("researchdatabases", input_records)
    assert next(output_records) == timdex.TimdexRecord(
        source="Research Databases",
        source_link="https://libguides.mit.edu/llba",
        timdex_record_id="researchdatabases:az-65257807",
        title="Linguistics and Language Behavior Abstracts (LLBA)",
        citation="Linguistics and Language Behavior Abstracts (LLBA). "
        "researchdatabases. https://libguides.mit.edu/llba",
        content_type=["researchdatabases"],
        dates=[
            timdex.Date(value="2022-01-28T22:15:37", kind="Created"),
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
        RESEARCHDATABASES_FIXTURES_PREFIX
        + "/research_databases_record_optional_fields_blank.xml"
    )
    output_records = SpringshareOaiDc("researchdatabases", input_records)
    assert (
        next(output_records)
        == RESEARCHDATABASES_BLANK_OR_MISSING_OPTIONAL_FIELDS_TIMDEX
    )


def test_research_databases_transform_with_optional_fields_missing_transforms_correctly():
    input_records = parse_xml_records(
        RESEARCHDATABASES_FIXTURES_PREFIX
        + "/research_databases_record_optional_fields_missing.xml"
    )
    output_records = SpringshareOaiDc("researchdatabases", input_records)
    assert (
        next(output_records)
        == RESEARCHDATABASES_BLANK_OR_MISSING_OPTIONAL_FIELDS_TIMDEX
    )
