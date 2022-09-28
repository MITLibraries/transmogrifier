import logging

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
            "Charles J. Connick Stained Glass Foundation Collection, VC-0002, box X. "
            "Massachusetts Institute of Technology, Department of Distinctive "
            "Collections, Cambridge, Massachusetts."
        ),
        contributors=[
            timdex.Contributor(
                value="Connick, Charles J. ( Charles Jay )",
                identifier=["https://lccn.loc.gov/nr99025157"],
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
        content_type=["Archival materials", "Correspondence"],
        contents=[
            "This collection is organized into ten series:",
            "Series 1. Charles J. Connick and Connick Studio documents",
            "Series 2. Charles J. Connick Studio and Associates job information",
            "Series 3. Charles J. Connick Stained Glass Foundation documents",
        ],
        dates=[
            timdex.Date(
                kind="creation",
                note="approximate",
                range=timdex.Date_Range(gte="1905", lte="2012"),
            )
        ],
        holdings=[
            timdex.Holding(
                note="Some originals are here",
            ),
            timdex.Holding(
                note="Some originals are there",
            ),
            timdex.Holding(location="Yet more originals are here"),
        ],
        identifiers=[timdex.Identifier(value="1234", kind="Collection Identifier")],
        languages=["English", "French"],
        locations=[timdex.Location(value="Boston, MA")],
        notes=[
            timdex.Note(
                value=[
                    "Charles J. Connick (1875-1945) was an American stained glass artist "
                    "whose work may be found in cities all across the United States. "
                    "Connick's works in the Arts and Crafts movement and beyond uniquely "
                    "combined ancient and modern techniques and also sparked a revival "
                    "of medieval European stained glass craftsmanship. Connick studied "
                    "symbols and the interaction between light, color and glass, as well "
                    "as the crucial connection between the stained glass window and its "
                    "surrounding architecture.",
                    "Connick founded his own studio in 1912 in Boston.",
                ],
                kind="Biographical Note",
            ),
            timdex.Note(
                value=[
                    "The Charles J. Connick Stained Glass Foundation Collection contains "
                    "documents, photographs, slides, film, periodicals, articles, "
                    "clippings, lecture transcripts, tools, sketches, designs and "
                    "cartoons (full size stained glass window designs), stained glass, "
                    "and ephemera.",
                    "The primary reference material is the job information.  In "
                    "particular, the job files (boxes 7-9) are used most often in "
                    "research.  Job files list specific information for each job "
                    "performed by the studio.",
                ],
                kind="Scope and Contents",
            ),
            timdex.Note(
                value=[
                    "Affiches americaines",
                    "San Domingo:",
                    "Imprimerie",
                    "royale du Cap, 1782. Nos. 30, 35.",
                ],
                kind="Bibliography",
            ),
        ],
    )


def test_ead_record_with_missing_archdesc_logs_error(caplog):
    ead_xml_records = parse_xml_records(
        "tests/fixtures/ead/ead_record_missing_archdesc.xml"
    )
    output_records = Ead("aspace", ead_xml_records)
    assert len(list(output_records)) == 0
    assert output_records.processed_record_count == 1
    assert (
        "transmogrifier.sources.ead",
        logging.ERROR,
        "Record ID repositories/2/resources/4 is missing archdesc element",
    ) in caplog.record_tuples


def test_ead_record_with_missing_archdesc_did_logs_error(caplog):
    ead_xml_records = parse_xml_records(
        "tests/fixtures/ead/ead_record_missing_archdesc_did.xml"
    )
    output_records = Ead("aspace", ead_xml_records)
    assert len(list(output_records)) == 0
    assert output_records.processed_record_count == 1
    assert (
        "transmogrifier.sources.ead",
        logging.ERROR,
        "Record ID repositories/2/resources/3 is missing archdesc > did element",
    ) in caplog.record_tuples


def test_ead_record_with_attribute_and_subfield_variations_transforms_correctly():
    ead_xml_records = parse_xml_records(
        "tests/fixtures/ead/ead_record_attribute_and_subfield_variations.xml"
    )
    output_records = Ead("aspace", ead_xml_records)
    assert next(output_records) == timdex.TimdexRecord(
        source="MIT ArchivesSpace",
        source_link="https://archivesspace.mit.edu/repositories/2/resources/6",
        timdex_record_id="aspace:repositories-2-resources-6",
        title="Title string",
        alternate_titles=[timdex.AlternateTitle(value="Title with XML")],
        citation=(
            "Name with no attributes, Name with authfilenumber, Name with source, Name "
            "with blank authfilenumber, Name with blank source, Name with authfile and "
            "source, Name with blank authfile and source, Name with authfile and blank "
            "source, Name with blank authfile and blank source, Contributor with X M L. "
            "Title string. Archival materials, Correspondence. "
            "https://archivesspace.mit.edu/repositories/2/resources/6"
        ),
        content_type=[
            "Archival materials",
            "Correspondence",
        ],
        contributors=[
            timdex.Contributor(
                value="Name with no attributes",
            ),
            timdex.Contributor(
                value="Name with authfilenumber",
                identifier=["nr99025157"],
            ),
            timdex.Contributor(
                value="Name with source",
            ),
            timdex.Contributor(
                value="Name with blank authfilenumber",
            ),
            timdex.Contributor(
                value="Name with blank source",
            ),
            timdex.Contributor(
                value="Name with authfile and source",
                identifier=["https://lccn.loc.gov/nr99025157"],
            ),
            timdex.Contributor(
                value="Name with blank authfile and source",
            ),
            timdex.Contributor(
                value="Name with authfile and blank source",
                identifier=["nr99025157"],
            ),
            timdex.Contributor(
                value="Name with blank authfile and blank source",
            ),
            timdex.Contributor(
                value="Contributor with X M L",
                identifier=["https://lccn.loc.gov/nr99025157"],
            ),
            timdex.Contributor(
                value="Name with no attributes",
            ),
            timdex.Contributor(
                value="Name with authfilenumber",
                identifier=["nr99025157"],
            ),
            timdex.Contributor(
                value="Name with source",
            ),
            timdex.Contributor(
                value="Name with blank authfilenumber",
            ),
            timdex.Contributor(
                value="Name with blank source",
            ),
            timdex.Contributor(
                value="Name with authfile and source",
                identifier=["https://lccn.loc.gov/nr99025157"],
            ),
            timdex.Contributor(
                value="Name with blank authfile and source",
            ),
            timdex.Contributor(
                value="Name with authfile and blank source",
                identifier=["nr99025157"],
            ),
            timdex.Contributor(
                value="Name with blank authfile and blank source",
            ),
            timdex.Contributor(
                value="Contributor with X M L",
                identifier=["https://lccn.loc.gov/nr99025157"],
            ),
            timdex.Contributor(
                value="Name with no attributes",
                kind="Creator",
            ),
            timdex.Contributor(
                value="Name with authfilenumber",
                identifier=["nr99025157"],
                kind="Creator",
            ),
            timdex.Contributor(
                value="Name with source",
                kind="Creator",
            ),
            timdex.Contributor(
                value="Name with blank authfilenumber",
                kind="Creator",
            ),
            timdex.Contributor(
                value="Name with blank source",
                kind="Creator",
            ),
            timdex.Contributor(
                value="Name with authfile and source",
                identifier=["https://lccn.loc.gov/nr99025157"],
                kind="Creator",
            ),
            timdex.Contributor(
                value="Name with blank authfile and source",
                kind="Creator",
            ),
            timdex.Contributor(
                value="Name with authfile and blank source",
                identifier=["nr99025157"],
                kind="Creator",
            ),
            timdex.Contributor(
                value="Name with blank authfile and blank source",
                kind="Creator",
            ),
            timdex.Contributor(
                value="Contributor with X M L",
                identifier=["https://lccn.loc.gov/nr99025157"],
                kind="Creator",
            ),
        ],
        contents=["Data not enclosed in subelement"],
        dates=[
            timdex.Date(
                range=timdex.Date_Range(gte="1905", lte="2012"),
            ),
            timdex.Date(value="1905"),
            timdex.Date(
                range=timdex.Date_Range(gte="1905", lte="2012"),
            ),
            timdex.Date(value="1905"),
            timdex.Date(
                range=timdex.Date_Range(gte="1905", lte="2012"),
            ),
            timdex.Date(value="1905"),
            timdex.Date(
                kind="creation",
                range=timdex.Date_Range(gte="1905", lte="2012"),
            ),
            timdex.Date(kind="creation", value="1905"),
            timdex.Date(
                kind="creation",
                range=timdex.Date_Range(gte="1905", lte="2012"),
            ),
            timdex.Date(kind="creation", value="1905"),
            timdex.Date(
                kind="creation",
                note="approximate",
                range=timdex.Date_Range(gte="1905", lte="2012"),
            ),
            timdex.Date(kind="creation", note="approximate", value="1905"),
            timdex.Date(
                note="approximate",
                range=timdex.Date_Range(gte="1905", lte="2012"),
            ),
            timdex.Date(note="approximate", value="1905"),
            timdex.Date(
                note="approximate",
                range=timdex.Date_Range(gte="1905", lte="2012"),
            ),
            timdex.Date(note="approximate", value="1905"),
        ],
        holdings=[
            timdex.Holding(location="Data enclosed in subelement"),
        ],
        identifiers=[
            timdex.Identifier(
                value="Data enclosed in subelement", kind="Collection Identifier"
            )
        ],
        locations=[timdex.Location(value="Data enclosed in subelement")],
        notes=[
            timdex.Note(value=["Data with blank head tag"]),
            timdex.Note(value=["Data with no head tag"]),
            timdex.Note(value=["Data with blank head tag"]),
            timdex.Note(value=["Data with no head tag"]),
            timdex.Note(value=["Data with no head element"]),
        ],
    )


def test_ead_record_with_blank_optional_fields_transforms_correctly():
    ead_xml_records = parse_xml_records(
        "tests/fixtures/ead/ead_record_blank_optional_fields.xml"
    )
    output_records = Ead("aspace", ead_xml_records)
    assert next(output_records) == timdex.TimdexRecord(
        source="MIT ArchivesSpace",
        source_link="https://archivesspace.mit.edu/repositories/2/resources/2",
        timdex_record_id="aspace:repositories-2-resources-2",
        title="Title not provided",
        citation=(
            "Title not provided. Archival materials. "
            "https://archivesspace.mit.edu/repositories/2/resources/2"
        ),
        content_type=["Archival materials"],
    )


def test_ead_record_with_missing_optional_fields_transforms_correctly():
    ead_xml_records = parse_xml_records(
        "tests/fixtures/ead/ead_record_missing_optional_fields.xml"
    )
    output_records = Ead("aspace", ead_xml_records)
    assert next(output_records) == timdex.TimdexRecord(
        source="MIT ArchivesSpace",
        source_link="https://archivesspace.mit.edu/repositories/2/resources/5",
        timdex_record_id="aspace:repositories-2-resources-5",
        title="Title not provided",
        citation=(
            "Title not provided. Archival materials. "
            "https://archivesspace.mit.edu/repositories/2/resources/5"
        ),
        content_type=["Archival materials"],
    )


def test_crosswalk_type_value_blank_value():
    assert Ead.crosswalk_type_value("") == ""


def test_crosswalk_type_value_invalid_value():
    assert Ead.crosswalk_type_value("abcd") == "abcd"


def test_crosswalk_type_value_valid_value():
    assert Ead.crosswalk_type_value("acqinfo") == "Acquisition Information"
