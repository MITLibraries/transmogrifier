import transmogrifier.models as timdex
from transmogrifier.helpers import parse_xml_records
from transmogrifier.sources.ead import Ead


def test_ead_get_main_titles_titleproper():
    ead_xml_records = parse_xml_records(
        "tests/fixtures/ead/ead_record_titleproper_string.xml"
    )
    output_records = Ead("archivesspace", ead_xml_records)
    assert next(output_records) == timdex.TimdexRecord(
        source="MIT ArchivesSpace",
        source_link="https://archivesspace.mit.edu/repositories/2/resources/1",
        timdex_record_id="archivesspace:repositories-2-resources-1",
        title="Guide to the Charles J. Connick Stained Glass Foundation Collection",
        citation=(
            "Guide to the Charles J. Connick Stained Glass Foundation Collection. "
            "https://archivesspace.mit.edu/repositories/2/resources/1"
        ),
        content_type=["Not specified"],
    )


def test_ead_get_main_titles_titleproper_with_subelements():
    ead_xml_records = parse_xml_records(
        "tests/fixtures/ead/ead_record_titleproper_with_subelements.xml"
    )
    output_records = Ead("archivesspace", ead_xml_records)
    assert next(output_records) == timdex.TimdexRecord(
        source="MIT ArchivesSpace",
        source_link="https://archivesspace.mit.edu/repositories/2/resources/1",
        timdex_record_id="archivesspace:repositories-2-resources-1",
        title=(
            "Guide to the Charles J. Connick Stained Glass Foundation Collection,"
            "VC.0002"
        ),
        citation=(
            "Guide to the Charles J. Connick Stained Glass Foundation Collection,"
            "VC.0002. "
            "https://archivesspace.mit.edu/repositories/2/resources/1"
        ),
        content_type=["Not specified"],
    )


def test_ead_get_main_titles_multiple_titleproper():
    ead_xml_records = parse_xml_records(
        "tests/fixtures/ead/ead_record_multiple_titleproper.xml"
    )
    output_records = Ead("archivesspace", ead_xml_records)
    assert next(output_records) == timdex.TimdexRecord(
        source="MIT ArchivesSpace",
        source_link="https://archivesspace.mit.edu/repositories/2/resources/1",
        timdex_record_id="archivesspace:repositories-2-resources-1",
        title=(
            "Guide to the Charles J. Connick Stained Glass Foundation Collection,"
            "VC.0002"
        ),
        alternate_titles=[timdex.AlternateTitle(value="Title 2,VC.0002")],
        citation=(
            "Guide to the Charles J. Connick Stained Glass Foundation Collection,"
            "VC.0002. "
            "https://archivesspace.mit.edu/repositories/2/resources/1"
        ),
        content_type=["Not specified"],
    )


# def test_ead_record_all_fields_transform_correctly():
#     assert False

# def test_ead_record_with_missing_optional_fields_transforms_correctly():
#     assert False


# def test_ead_record_with_blank_optional_fields_transforms_correctly():
#     assert False


# def test_ead_with_attribute_and_subfield_variations_transforms_correctly():
#     assert False
