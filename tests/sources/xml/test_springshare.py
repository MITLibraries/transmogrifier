# ruff: noqa: E501
import logging

import pytest
from bs4 import BeautifulSoup

import transmogrifier.models as timdex
from transmogrifier.exceptions import SkippedRecordEvent
from transmogrifier.sources.xml.springshare import SpringshareOaiDc

SPRINGSHARE_FIXTURES_PREFIX = "tests/fixtures/oai_dc/springshare"
LIBGUIDES_FIXTURES_PREFIX = f"{SPRINGSHARE_FIXTURES_PREFIX}/libguides"
RESEARCHDATABASES_FIXTURES_PREFIX = f"{SPRINGSHARE_FIXTURES_PREFIX}/research_databases"


def create_oaidc_source_record_stub(
    header_insert: str = "", metadata_insert: str = ""
) -> BeautifulSoup:

    xml_str = f"""
        <records>
            <record>
                <header>
                    {header_insert}
                </header>
                <metadata>
                    <oai_dc:dc xmlns:oai_dc="http://www.openarchives.org/OAI/2.0/oai_dc/"
                        xmlns:dc="http://purl.org/dc/elements/1.1/"
                        xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
                        xsi:schemaLocation="http://www.openarchives.org/OAI/2.0/oai_dc/ http://www.openarchives.org/OAI/2.0/oai_dc.xsd">
                        {metadata_insert}
                    </oai_dc:dc>
                </metadata>
            </record>
        <records
    """
    return BeautifulSoup(xml_str, "xml")


#################################
# Springshare - Source-Agnostic
#################################


def test_get_dates_success():
    source_record = create_oaidc_source_record_stub(
        header_insert=(
            """
            <identifier>oai:libguides.com:guides/175846</identifier>
            """
        ),
        metadata_insert=(
            """
            <dc:date>January 1st, 2000</dc:date>
            """
        ),
    )
    assert SpringshareOaiDc.get_dates(source_record) == [
        timdex.Date(kind="Created", value="2000-01-01T00:00:00")
    ]


def test_get_dates_transforms_correctly_if_optional_fields_blank():
    source_record = create_oaidc_source_record_stub(
        header_insert=(
            """
            <identifier>oai:libguides.com:guides/175846</identifier>
            """
        ),
        metadata_insert=(
            """
            <dc:date></dc:date>
            """
        ),
    )
    assert SpringshareOaiDc.get_dates(source_record) is None


def test_get_dates_transforms_correctly_if_optional_fields_missing():
    source_record = create_oaidc_source_record_stub(
        header_insert=(
            """
            <identifier>oai:libguides.com:guides/175846</identifier>
            """
        )
    )
    assert SpringshareOaiDc.get_dates(source_record) is None


def test_get_dates_transforms_correctly_and_logs_error_if_date_invalid(
    caplog,
):
    caplog.set_level(logging.DEBUG)
    source_record = create_oaidc_source_record_stub(
        header_insert=(
            """
            <identifier>oai:libguides.com:guides/175846</identifier>
            """
        ),
        metadata_insert=(
            """
            <dc:date>INVALID</dc:date>
            """
        ),
    )
    assert SpringshareOaiDc.get_dates(source_record) is None
    assert (
        "Record ID guides/175846 has a date that cannot be parsed: Unknown string format: INVALID"
        in caplog.text
    )


def test_get_links_success():
    source_record = create_oaidc_source_record_stub(
        header_insert=(
            """
            <identifier>oai:libguides.com:guides/175846</identifier>
            """
        ),
        metadata_insert=(
            """
            <dc:identifier>https://libguides.mit.edu/materials</dc:identifier>
            """
        ),
    )
    assert SpringshareOaiDc("libguides", iter(())).get_links(
        source_record=source_record
    ) == [
        timdex.Link(
            kind="LibGuide URL",
            text="LibGuide URL",
            url="https://libguides.mit.edu/materials",
        )
    ]


def test_get_links_transforms_correctly_if_required_fields_blank():
    source_record = create_oaidc_source_record_stub(
        header_insert=(
            """
            <identifier>oai:libguides.com:guides/175846</identifier>
            """
        ),
        metadata_insert=(
            """
            <dc:identifier></dc:identifier>
            """
        ),
    )
    assert SpringshareOaiDc("libguides", iter(())).get_links(source_record) is None


def test_get_links_transforms_correctly_if_required_fields_missing():
    source_record = create_oaidc_source_record_stub(
        header_insert=(
            """
            <identifier>oai:libguides.com:guides/175846</identifier>
            """
        )
    )
    assert SpringshareOaiDc("libguides", iter(())).get_links(source_record) is None


def test_get_source_link_success():
    source_record = create_oaidc_source_record_stub(
        metadata_insert=(
            """
            <dc:identifier>https://libguides.mit.edu/materials</dc:identifier>
            """
        )
    )
    springshare = SpringshareOaiDc("libguides", iter(source_record))
    assert (
        springshare.get_source_link(source_record)
        == "https://libguides.mit.edu/materials"
    )


def test_get_source_link_raises_skipped_record_event_if_required_fields_blank():
    source_record = create_oaidc_source_record_stub(
        metadata_insert=(
            """
            <dc:identifier></dc:identifier>
            """
        )
    )
    springshare = SpringshareOaiDc("libguides", iter(source_record))
    with pytest.raises(
        SkippedRecordEvent,
        match=(
            r"Record skipped because 'source_link' could not be derived. "
            r"The 'identifier' was either missing from the header element or blank."
        ),
    ):
        springshare.get_source_link(source_record)


def test_get_source_link_raises_skipped_record_event_if_required_fields_missing():
    source_record = create_oaidc_source_record_stub(
        metadata_insert=(
            """
            <dc:identifier></dc:identifier>
            """
        )
    )
    springshare = SpringshareOaiDc("libguides", iter(source_record))
    with pytest.raises(
        SkippedRecordEvent,
        match=(
            r"Record skipped because 'source_link' could not be derived. "
            r"The 'identifier' was either missing from the header element or blank."
        ),
    ):
        springshare.get_source_link(source_record)


###########################
# Springshare - LibGuides
###########################


def test_springshare_libguides_transform_with_all_fields_transforms_correctly():
    source_records = SpringshareOaiDc.parse_source_file(
        f"{LIBGUIDES_FIXTURES_PREFIX}/libguides_record_all_fields.xml"
    )
    output_records = SpringshareOaiDc("libguides", source_records)
    timdex_record = output_records.transform(next(output_records.source_records))
    assert timdex_record == timdex.TimdexRecord(
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
        publishers=[timdex.Publisher(name="MIT Libraries")],
        subjects=[
            timdex.Subject(
                value=["Engineering", "Science"],
                kind="Subject scheme not provided",
            ),
        ],
        summary=["Useful databases and other research tips for materials science."],
    )


def test_springshare_libguides_transform_with_optional_fields_blank_transforms_correctly():
    source_records = SpringshareOaiDc.parse_source_file(
        f"{LIBGUIDES_FIXTURES_PREFIX}/libguides_record_optional_fields_blank.xml"
    )
    output_records = SpringshareOaiDc("libguides", source_records)
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


def test_springshare_libguides_transform_with_optional_fields_missing_transforms_correctly():
    source_records = SpringshareOaiDc.parse_source_file(
        f"{LIBGUIDES_FIXTURES_PREFIX}/libguides_record_optional_fields_missing.xml"
    )
    output_records = SpringshareOaiDc("libguides", source_records)
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


####################################
# Springshare - Research Databases
####################################


def test_springshare_research_databases_transform_with_all_fields_transforms_correctly():
    source_records = SpringshareOaiDc.parse_source_file(
        f"{RESEARCHDATABASES_FIXTURES_PREFIX}/research_databases_record_all_fields.xml"
    )
    output_records = SpringshareOaiDc("researchdatabases", source_records)
    timdex_record = output_records.transform(next(output_records.source_records))
    assert timdex_record == timdex.TimdexRecord(
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


def test_springshare_research_databases_transform_with_optional_fields_blank_transforms_correctly():
    source_records = SpringshareOaiDc.parse_source_file(
        RESEARCHDATABASES_FIXTURES_PREFIX
        + "/research_databases_record_optional_fields_blank.xml"
    )
    output_records = SpringshareOaiDc("researchdatabases", source_records)
    timdex_record = output_records.transform(next(output_records.source_records))
    assert timdex_record == timdex.TimdexRecord(
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


def test_springshare_research_databases_transform_with_optional_fields_missing_transforms_correctly():
    source_records = SpringshareOaiDc.parse_source_file(
        RESEARCHDATABASES_FIXTURES_PREFIX
        + "/research_databases_record_optional_fields_missing.xml"
    )
    output_records = SpringshareOaiDc("researchdatabases", source_records)
    timdex_record = output_records.transform(next(output_records.source_records))
    assert timdex_record == timdex.TimdexRecord(
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
