import transmogrifier.models as timdex
from tests.sources.xml.test_springshare import (
    SPRINGSHARE_FIXTURES_PREFIX,
)
from transmogrifier.sources.xml.libguides import LibGuides

LIBGUIDES_FIXTURES_PREFIX = f"{SPRINGSHARE_FIXTURES_PREFIX}/libguides"


def test_libguides_transform_with_all_fields_transforms_correctly():
    source_records = LibGuides.parse_source_file(
        f"{LIBGUIDES_FIXTURES_PREFIX}/libguides_record_all_fields.xml"
    )
    output_records = LibGuides("libguides", source_records)
    timdex_record = output_records.transform(next(output_records.source_records))
    assert timdex_record == timdex.TimdexRecord(
        source="LibGuides",
        source_link="https://libguides.mit.edu/materials",
        timdex_record_id="libguides:guides-175846",
        title="Materials Science & Engineering",
        citation="Materials Science & Engineering. MIT Libraries. libguides. "
        "https://libguides.mit.edu/materials",
        content_type=["libguides"],
        contributors=None,
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
        publishers=[timdex.Publisher(name="MIT Libraries")],
        subjects=[
            timdex.Subject(
                value=["Engineering", "Science"],
                kind="Subject scheme not provided",
            ),
        ],
        summary=["Useful databases and other research tips for materials science."],
    )


def test_libguides_transform_with_optional_fields_blank_transforms_correctly():
    source_records = LibGuides.parse_source_file(
        f"{LIBGUIDES_FIXTURES_PREFIX}/libguides_record_optional_fields_blank.xml"
    )
    output_records = LibGuides("libguides", source_records)
    timdex_record = output_records.transform(next(output_records.source_records))
    assert timdex_record == timdex.TimdexRecord(
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


def test_libguides_transform_with_optional_fields_missing_transforms_correctly():
    source_records = LibGuides.parse_source_file(
        f"{LIBGUIDES_FIXTURES_PREFIX}/libguides_record_optional_fields_missing.xml"
    )
    output_records = LibGuides("libguides", source_records)
    timdex_record = output_records.transform(next(output_records.source_records))
    assert timdex_record == timdex.TimdexRecord(
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
