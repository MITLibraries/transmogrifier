from bs4 import BeautifulSoup

import transmogrifier.models as timdex
from transmogrifier.sources.xml.digital_collections import DigitalCollections


def create_digital_collections_source_record_stub(xml_insert: str = "") -> BeautifulSoup:
    xml_string = f"""
        <records>
         <record xmlns="http://www.openarchives.org/OAI/2.0/"
         xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
          <header>
           <identifier>oai:dome.mit.edu:1721.3/77697</identifier>
           <datestamp>2024-01-01T00:00:00Z</datestamp>
          </header>
          <metadata>
           <dim:dim xmlns:dim="http://www.dspace.org/xmlns/dspace/dim"
           xmlns:doc="http://www.lyncode.com/xoai"
           xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
           xsi:schemaLocation="http://www.dspace.org/xmlns/dspace/dim
           http://www.dspace.org/schema/dim.xsd">
           {xml_insert}
           </dim:dim>
          </metadata>
         </record>
        </records>
        """
    return BeautifulSoup(xml_string, "xml")


def test_get_funding_information_returns_none_with_sponsorship_field():
    source_record = create_digital_collections_source_record_stub("""
        <dim:field mdschema="dc" element="description" qualifier="sponsorship"
        >National Science Foundation</dim:field>
        """)
    assert DigitalCollections.get_funding_information(source_record) is None


def test_get_notes_success():
    source_record = create_digital_collections_source_record_stub("""
        <dim:field mdschema="vra" element="culturalContext">American</dim:field>
        <dim:field mdschema="vra" element="technique">construction</dim:field>
        <dim:field mdschema="dc" element="format" qualifier="medium">stone</dim:field>
        """)
    assert DigitalCollections.get_notes(source_record) == [
        timdex.Note(value=["American"], kind="culturalContext"),
        timdex.Note(value=["construction"], kind="technique"),
        timdex.Note(value=["stone"], kind="medium"),
    ]


def test_get_notes_transforms_correctly_if_fields_blank():
    source_record = create_digital_collections_source_record_stub("""
        <dim:field mdschema="vra" element="culturalContext" />
        <dim:field mdschema="vra" element="technique" />
        <dim:field mdschema="dc" element="format" qualifier="medium" />
        """)
    assert DigitalCollections.get_notes(source_record) is None


def test_get_notes_transforms_correctly_if_fields_missing():
    source_record = create_digital_collections_source_record_stub()
    assert DigitalCollections.get_notes(source_record) is None


def test_get_notes_excludes_dc_description_fields():
    source_record = create_digital_collections_source_record_stub("""
        <dim:field mdschema="dc" element="description" qualifier="embargo"
        >2026-01</dim:field>
        """)
    assert DigitalCollections.get_notes(source_record) is None


def test_get_provider_success():
    source_record = create_digital_collections_source_record_stub("""
        <dim:field mdschema="dc" element="publisher" qualifier="institution"
        >Massachusetts Institute of Technology. Libraries.</dim:field>
        """)
    assert (
        DigitalCollections.get_provider(source_record)
        == "Massachusetts Institute of Technology. Libraries."
    )


def test_get_provider_transforms_correctly_if_fields_blank():
    source_record = create_digital_collections_source_record_stub(
        '<dim:field mdschema="dc" element="publisher" qualifier="institution" />'
    )
    assert DigitalCollections.get_provider(source_record) is None


def test_get_provider_transforms_correctly_if_fields_missing():
    source_record = create_digital_collections_source_record_stub()
    assert DigitalCollections.get_provider(source_record) is None


def test_get_publishers_success():
    source_record = create_digital_collections_source_record_stub("""
        <dim:field mdschema="dc" element="publisher">Lincoln Laboratory</dim:field>
        """)
    assert DigitalCollections.get_publishers(source_record) == [
        timdex.Publisher(name="Lincoln Laboratory")
    ]


def test_get_publishers_excludes_institution_qualifier():
    source_record = create_digital_collections_source_record_stub("""
        <dim:field mdschema="dc" element="publisher">Lincoln Laboratory</dim:field>
        <dim:field mdschema="dc" element="publisher" qualifier="institution"
        >Massachusetts Institute of Technology. Libraries.</dim:field>
        """)
    assert DigitalCollections.get_publishers(source_record) == [
        timdex.Publisher(name="Lincoln Laboratory")
    ]


def test_get_publishers_transforms_correctly_if_institution_qualifier_present():
    source_record = create_digital_collections_source_record_stub("""
        <dim:field mdschema="dc" element="publisher" qualifier="institution"
        >Massachusetts Institute of Technology. Libraries.</dim:field>
        """)
    assert DigitalCollections.get_publishers(source_record) is None


def test_get_publishers_transforms_correctly_if_fields_blank():
    source_record = create_digital_collections_source_record_stub(
        '<dim:field mdschema="dc" element="publisher" />'
    )
    assert DigitalCollections.get_publishers(source_record) is None


def test_get_publishers_transforms_correctly_if_fields_missing():
    source_record = create_digital_collections_source_record_stub()
    assert DigitalCollections.get_publishers(source_record) is None


def test_get_subjects_success():
    source_record = create_digital_collections_source_record_stub("""
        <dim:field mdschema="dc" element="subject" qualifier="lcsh"
        >Land use, Urban</dim:field>
        <dim:field mdschema="dc" element="subject">City planning</dim:field>
        <dim:field mdschema="vra" element="worktype">Mosque</dim:field>
        """)
    assert DigitalCollections.get_subjects(source_record) == [
        timdex.Subject(value=["Land use, Urban"], kind="lcsh"),
        timdex.Subject(value=["City planning"], kind="Subject scheme not provided"),
        timdex.Subject(value=["Mosque"], kind="worktype"),
    ]


def test_get_subjects_with_worktype():
    source_record = create_digital_collections_source_record_stub("""
        <dim:field mdschema="vra" element="worktype">Palace</dim:field>
        """)
    assert DigitalCollections.get_subjects(source_record) == [
        timdex.Subject(value=["Palace"], kind="worktype"),
    ]


def test_get_subjects_transforms_correctly_if_fields_blank():
    source_record = create_digital_collections_source_record_stub("""
        <dim:field mdschema="dc" element="subject" />
        <dim:field mdschema="vra" element="worktype" />
        """)
    assert DigitalCollections.get_subjects(source_record) is None


def test_get_subjects_transforms_correctly_if_fields_missing():
    source_record = create_digital_collections_source_record_stub()
    assert DigitalCollections.get_subjects(source_record) is None


def test_get_summary_success():
    source_record = create_digital_collections_source_record_stub("""
        <dim:field mdschema="dc" element="description" qualifier="abstract"
        >Abstract text.</dim:field>
        <dim:field mdschema="dc" element="description">general view</dim:field>
        """)
    assert DigitalCollections.get_summary(source_record) == [
        "Abstract text.",
        "general view",
    ]


def test_get_summary_includes_unqualified_description():
    source_record = create_digital_collections_source_record_stub("""
        <dim:field mdschema="dc" element="description">exterior</dim:field>
        """)
    assert DigitalCollections.get_summary(source_record) == ["exterior"]


def test_get_summary_excludes_qualified_non_abstract_descriptions():
    source_record = create_digital_collections_source_record_stub("""
        <dim:field mdschema="dc" element="description" qualifier="embargo"
        >2026-01</dim:field>
        <dim:field mdschema="dc" element="description" qualifier="provenance"
        >Transferred from collection X.</dim:field>
        """)
    assert DigitalCollections.get_summary(source_record) is None


def test_get_summary_transforms_correctly_if_fields_blank():
    source_record = create_digital_collections_source_record_stub("""
        <dim:field mdschema="dc" element="description" qualifier="abstract" />
        <dim:field mdschema="dc" element="description" />
        """)
    assert DigitalCollections.get_summary(source_record) is None


def test_get_summary_transforms_correctly_if_fields_missing():
    source_record = create_digital_collections_source_record_stub()
    assert DigitalCollections.get_summary(source_record) is None
