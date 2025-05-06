import pytest
from bs4 import BeautifulSoup

import transmogrifier.models as timdex
from transmogrifier.exceptions import SkippedRecordEvent
from transmogrifier.sources.xml.oaidc import OaiDc


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


def test_oaidc_transform_with_all_fields_transforms_correctly():
    source_records = OaiDc.parse_source_file(
        "tests/fixtures/oai_dc/oaidc_record_all_fields.xml"
    )
    output_records = OaiDc("cool-repo", source_records)
    timdex_record = output_records.transform(next(output_records.source_records))
    assert timdex_record == timdex.TimdexRecord(
        source="A Cool Repository",
        source_link="https://example.com/guides/175846",
        timdex_record_id="cool-repo:guides-175846",
        title="Materials Science & Engineering",
        citation="Ye Li. Materials Science & Engineering. MIT Libraries. cool-repo. "
        "https://example.com/guides/175846",
        content_type=["cool-repo"],
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
        "tests/fixtures/oai_dc/oaidc_record_optional_fields_blank.xml"
    )
    output_records = OaiDc("cool-repo", source_records)
    timdex_record = output_records.transform(next(output_records.source_records))
    assert timdex_record == timdex.TimdexRecord(
        source="A Cool Repository",
        source_link="https://example.com/guides/175846",
        timdex_record_id="cool-repo:guides-175846",
        title="Materials Science & Engineering",
        citation="Materials Science & Engineering. cool-repo. "
        "https://example.com/guides/175846",
        content_type=["cool-repo"],
        format="electronic resource",
        identifiers=[
            timdex.Identifier(value="oai:libguides.com:guides/175846", kind="OAI-PMH")
        ],
    )


def test_oaidc_transform_with_optional_fields_missing_transforms_correctly():
    source_records = OaiDc.parse_source_file(
        "tests/fixtures/oai_dc/oaidc_record_optional_fields_missing.xml"
    )
    output_records = OaiDc("cool-repo", source_records)
    timdex_record = output_records.transform(next(output_records.source_records))
    assert timdex_record == timdex.TimdexRecord(
        source="A Cool Repository",
        source_link="https://example.com/guides/175846",
        timdex_record_id="cool-repo:guides-175846",
        title="Materials Science & Engineering",
        citation="Materials Science & Engineering. cool-repo. "
        "https://example.com/guides/175846",
        content_type=["cool-repo"],
        format="electronic resource",
        identifiers=[
            timdex.Identifier(value="oai:libguides.com:guides/175846", kind="OAI-PMH")
        ],
    )


def test_get_content_type_success():
    assert OaiDc("cool-repo", iter(())).get_content_type() == ["cool-repo"]


def test_get_content_type_raises_key_error_if_source_blank():
    with pytest.raises(KeyError):
        OaiDc("", iter(())).get_content_type()


def test_get_content_type_raises_key_error_if_source_missing():
    with pytest.raises(KeyError):
        OaiDc(None, iter(())).get_content_type()


def test_get_contributors_success():
    source_record = create_oaidc_source_record_stub(
        metadata_insert=(
            """
            <dc:creator>Ye Li</dc:creator>
            """
        )
    )
    assert OaiDc.get_contributors(source_record) == [
        timdex.Contributor(
            value="Ye Li",
            kind="Creator",
        )
    ]


def test_get_contributors_transforms_correctly_if_fields_blank():
    source_record = create_oaidc_source_record_stub(
        metadata_insert=(
            """
            <dc:creator></dc:creator>
            """
        )
    )
    assert OaiDc.get_contributors(source_record) is None


def test_get_contributors_transforms_correctly_if_fields_missing():
    source_record = create_oaidc_source_record_stub()
    assert OaiDc.get_contributors(source_record) is None


def test_get_dates_success():
    source_record = create_oaidc_source_record_stub(
        header_insert=(
            """
            <identifier>oai:libguides.com:guides/175846</identifier>
            """
        ),
        metadata_insert=(
            """
            <dc:date>2008-06-19T17:55:27</dc:date>
            """
        ),
    )
    assert OaiDc.get_dates(source_record) == [
        timdex.Date(kind="Unknown", value="2008-06-19T17:55:27")
    ]


def test_get_dates_transforms_correctly_if_fields_blank():
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
    assert OaiDc.get_dates(source_record) is None


def test_get_dates_transforms_correctly_if_fields_missing():
    source_record = create_oaidc_source_record_stub(
        header_insert=(
            """
            <identifier>oai:libguides.com:guides/175846</identifier>
            """
        )
    )
    assert OaiDc.get_dates(source_record) is None


def test_get_dates_transforms_correctly_if_date_invalid():
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
    assert OaiDc.get_dates(source_record) is None


def test_get_identifiers_success():
    source_record = create_oaidc_source_record_stub(
        header_insert=(
            """
            <identifier>oai:libguides.com:guides/175846</identifier>
            """
        )
    )
    assert OaiDc.get_identifiers(source_record) == [
        timdex.Identifier(value="oai:libguides.com:guides/175846", kind="OAI-PMH")
    ]


def test_get_identifiers_transforms_correctly_if_fields_blank():
    source_record = create_oaidc_source_record_stub(
        header_insert=(
            """
            <identifier></identifier>
            """
        )
    )
    assert OaiDc.get_identifiers(source_record) is None


def test_get_identifiers_transforms_correctly_if_fields_missing():
    source_record = create_oaidc_source_record_stub()
    assert OaiDc.get_identifiers(source_record) is None


def test_get_publishers_success():
    source_record = create_oaidc_source_record_stub(
        metadata_insert=(
            """
            <dc:publisher>MIT Libraries</dc:publisher>
            """
        )
    )
    assert OaiDc.get_publishers(source_record) == [timdex.Publisher(name="MIT Libraries")]


def test_get_publishers_transforms_correctly_if_fields_blank():
    source_record = create_oaidc_source_record_stub(
        metadata_insert=(
            """
            <dc:publisher></dc:publisher>
            """
        )
    )
    assert OaiDc.get_publishers(source_record) is None


def test_get_publishers_transforms_correctly_if_fields_missing():
    source_record = create_oaidc_source_record_stub()
    assert OaiDc.get_publishers(source_record) is None


def test_get_subjects_success():
    source_record = create_oaidc_source_record_stub(
        metadata_insert=(
            """
            <dc:subject>Engineering</dc:subject>
            <dc:subject>Science</dc:subject>
            """
        )
    )
    assert OaiDc.get_subjects(source_record) == [
        timdex.Subject(
            value=["Engineering", "Science"], kind="Subject scheme not provided"
        )
    ]


def test_get_subjects_transforms_correctly_if_fields_blank():
    source_record = create_oaidc_source_record_stub(
        metadata_insert=(
            """
            <dc:subject></dc:subject>
            """
        )
    )
    assert OaiDc.get_subjects(source_record) is None


def test_get_subjects_transforms_correctly_if_fields_missing():
    source_record = create_oaidc_source_record_stub()
    assert OaiDc.get_subjects(source_record) is None


def test_get_summary_success():
    source_record = create_oaidc_source_record_stub(
        metadata_insert=(
            "<dc:description>"
            "Useful databases and other research tips for materials science."
            "</dc:description>"
        )
    )
    assert OaiDc.get_summary(source_record) == [
        "Useful databases and other research tips for materials science."
    ]


def test_get_summary_transforms_properly_if_fields_blank():
    source_record = create_oaidc_source_record_stub(
        metadata_insert=(
            """
            <dc:description></dc:description>
            """
        )
    )
    assert OaiDc.get_summary(source_record) is None


def test_get_summary_transforms_properly_if_fields_missing():
    source_record = create_oaidc_source_record_stub()
    assert OaiDc.get_summary(source_record) is None


def test_get_main_titles_success():
    source_record = create_oaidc_source_record_stub(
        metadata_insert=(
            """
            <dc:title>Materials Science &amp; Engineering</dc:title>
            """
        )
    )
    assert OaiDc.get_main_titles(source_record) == ["Materials Science & Engineering"]


def test_get_main_titles_transforms_properly_if_fields_blank():
    source_record = create_oaidc_source_record_stub(
        metadata_insert=(
            """
            <dc:title></dc:title>
            """
        )
    )
    assert OaiDc.get_main_titles(source_record) == []


def test_get_main_titles_transforms_properly_if_fields_missing():
    source_record = create_oaidc_source_record_stub()
    assert OaiDc.get_main_titles(source_record) == []


def test_get_source_record_id_success():
    source_record = create_oaidc_source_record_stub(
        header_insert=(
            """
            <identifier>oai:libguides.com:guides/175846</identifier>
            """
        )
    )
    assert OaiDc.get_source_record_id(source_record) == "guides/175846"


def test_get_source_record_id_raises_skipped_record_event_if_fields_blank():
    source_record = create_oaidc_source_record_stub(
        header_insert=(
            """
            <identifier></identifier>
            """
        )
    )
    with pytest.raises(
        SkippedRecordEvent,
        match=(
            "Record skipped because 'source_record_id' could not be derived. "
            "The 'identifier' was either missing from the header element or blank."
        ),
    ):
        OaiDc.get_source_record_id(source_record)


def test_get_source_record_id_raises_skipped_record_event_if_fields_missing():
    source_record = create_oaidc_source_record_stub()
    with pytest.raises(
        SkippedRecordEvent,
        match=(
            "Record skipped because 'source_record_id' could not be derived. "
            "The 'identifier' was either missing from the header element or blank."
        ),
    ):
        OaiDc.get_source_record_id(source_record)
