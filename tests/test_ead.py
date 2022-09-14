import transmogrifier.models as timdex
from transmogrifier.helpers import parse_xml_records
from transmogrifier.sources.ead import Ead


def test_ead_record_all_fields_transform_correctly():
    ead_xml_records = parse_xml_records("tests/fixtures/ead/ead_record_all_fields.xml")
    output_records = Ead("aspace", ead_xml_records)
    assert next(output_records) == timdex.TimdexRecord(
        source="MIT ArchivesSpace",
        source_link="https://archivesspace.mit.edu/repositories/2/resources/1",
        timdex_record_id="aspace:repositories-2-resources-1",
        title="Charles J. Connick Stained Glass Foundation Collection",
        alternate_titles=[
            timdex.AlternateTitle(value="Title 2"),
            timdex.AlternateTitle(value="Title 3"),
        ],
        citation=(
            "Connick, Charles J. (Charles Jay), Author, Unknown, Name 2, Name 3, Name 4. "
            "Charles J. Connick Stained Glass Foundation Collection. "
            "https://archivesspace.mit.edu/repositories/2/resources/1"
        ),
        contributors=[
            timdex.Contributor(
                value="Connick, Charles J. (Charles Jay)",
                identifier=["https://lccn.loc.gov/nr99025157"],
                kind="Creator",
            ),
            timdex.Contributor(
                value="Author, Unknown",
                identifier=["nr9902"],
                kind="Creator",
            ),
            timdex.Contributor(
                value="Name 2",
                identifier=["http://viaf.org/viaf/nr97"],
                kind="Creator",
            ),
            timdex.Contributor(
                value="Name 3",
                identifier=["https://snaccooperative.org/view/nr9957"],
                kind="Creator",
            ),
            timdex.Contributor(
                value="Name 4",
                kind="Creator",
            ),
            timdex.Contributor(
                value="Name 5",
                identifier=["http://viaf.org/viaf/nr99025435"],
            ),
        ],
        content_type=["Not specified"],
    )


def test_ead_record_with_missing_archdesc_raises_error(caplog):
    ead_xml_records = parse_xml_records(
        "tests/fixtures/ead/ead_record_missing_archdesc.xml"
    )
    output_records = Ead("aspace", ead_xml_records)
    assert len(list(output_records)) == 0
    assert output_records.processed_record_count == 1
    assert "Record is missing archdesc element" in caplog.text


def test_ead_record_with_missing_archdesc_did_raises_error(caplog):
    ead_xml_records = parse_xml_records(
        "tests/fixtures/ead/ead_record_missing_archdesc_did.xml"
    )
    output_records = Ead("aspace", ead_xml_records)
    assert len(list(output_records)) == 0
    assert output_records.processed_record_count == 1
    assert "Record is missing archdesc > did element" in caplog.text


def test_ead_record_with_blank_optional_fields_transforms_correctly():
    ead_xml_records = parse_xml_records(
        "tests/fixtures/ead/ead_record_blank_optional_fields.xml"
    )
    output_records = Ead("aspace", ead_xml_records)
    assert next(output_records) == timdex.TimdexRecord(
        source="MIT ArchivesSpace",
        source_link="https://archivesspace.mit.edu/repositories/2/resources/3",
        timdex_record_id="aspace:repositories-2-resources-3",
        title="Title not provided",
        citation=(
            "Title not provided. https://archivesspace.mit.edu/repositories/2/resources/3"
        ),
        content_type=["Not specified"],
    )


def test_ead_record_with_missing_optional_fields_transforms_correctly():
    ead_xml_records = parse_xml_records(
        "tests/fixtures/ead/ead_record_missing_optional_fields.xml"
    )
    output_records = Ead("aspace", ead_xml_records)
    assert next(output_records) == timdex.TimdexRecord(
        source="MIT ArchivesSpace",
        source_link="https://archivesspace.mit.edu/repositories/2/resources/2",
        timdex_record_id="aspace:repositories-2-resources-2",
        title="Title not provided",
        citation=(
            "Title not provided. https://archivesspace.mit.edu/repositories/2/resources/2"
        ),
        content_type=["Not specified"],
    )


def test_ead_get_main_titles__extracts_correctly():
    ead_xml_records = parse_xml_records("tests/fixtures/ead/ead_record_all_fields.xml")
    ead = Ead("aspace", ead_xml_records)
    assert ead.get_main_titles(next(ead_xml_records)) == [
        "Charles J. Connick Stained Glass Foundation Collection",
        "Title 2",
        "Title 3",
    ]


def test_ead_get_main_titles_no_unittitle_extracts_correctly():
    ead_xml_records = parse_xml_records(
        "tests/fixtures/ead/ead_record_missing_archdesc_did.xml"
    )
    ead = Ead("aspace", ead_xml_records)
    assert ead.get_main_titles(next(ead_xml_records)) == []
