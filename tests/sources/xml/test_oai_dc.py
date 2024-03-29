import transmogrifier.models as timdex
from transmogrifier.sources.xml.oaidc import OaiDc

FIXTURES_PREFIX = "tests/fixtures/oai_dc"

BLANK_OR_MISSING_OPTIONAL_FIELDS_TIMDEX = timdex.TimdexRecord(
    source="LibGuides",
    source_link="https://libguides.mit.edu/guides/175846",
    timdex_record_id="libguides:guides-175846",
    title="Materials Science & Engineering",
    citation="Materials Science & Engineering. libguides. "
    "https://libguides.mit.edu/guides/175846",
    content_type=["libguides"],
    format="electronic resource",
    identifiers=[
        timdex.Identifier(value="oai:libguides.com:guides/175846", kind="OAI-PMH")
    ],
)


def test_oaidctransform_with_all_fields_transforms_correctly():
    source_records = OaiDc.parse_source_file(
        f"{FIXTURES_PREFIX}/oaidc_record_all_fields.xml"
    )
    output_records = OaiDc("libguides", source_records)
    assert next(output_records) == timdex.TimdexRecord(
        source="LibGuides",
        source_link="https://libguides.mit.edu/guides/175846",
        timdex_record_id="libguides:guides-175846",
        title="Materials Science & Engineering",
        citation="Ye Li. Materials Science & Engineering. MIT Libraries. libguides. "
        "https://libguides.mit.edu/guides/175846",
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
        publishers=[timdex.Publisher(name="MIT Libraries")],
        subjects=[
            timdex.Subject(
                value=["Engineering", "Science"],
                kind="Subject scheme not provided",
            ),
        ],
        summary=["Useful databases and other research tips for materials science."],
    )


def test_oaidc_transform_with_optional_fields_blank_transforms_correctly():
    source_records = OaiDc.parse_source_file(
        f"{FIXTURES_PREFIX}/oaidc_record_optional_fields_blank.xml"
    )
    output_records = OaiDc("libguides", source_records)
    assert next(output_records) == BLANK_OR_MISSING_OPTIONAL_FIELDS_TIMDEX


def test_oaidc_transform_with_optional_fields_missing_transforms_correctly():
    source_records = OaiDc.parse_source_file(
        f"{FIXTURES_PREFIX}/oaidc_record_optional_fields_missing.xml"
    )
    output_records = OaiDc("libguides", source_records)
    assert next(output_records) == BLANK_OR_MISSING_OPTIONAL_FIELDS_TIMDEX


def test_oaidc_generic_date():
    source_records = OaiDc.parse_source_file(
        f"{FIXTURES_PREFIX}/oaidc_record_valid_generic_date.xml"
    )
    transformer_instance = OaiDc("libguides", source_records)
    xml = next(transformer_instance.source_records)
    assert transformer_instance.get_dates("test_source_record_id", xml) == [
        timdex.Date(kind="Unknown", note=None, range=None, value="2008-06-19T17:55:27")
    ]
