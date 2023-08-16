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
        identifiers=[timdex.Identifier(value="1234", kind="Collection Identifier")],
        languages=["English", "French"],
        locations=[timdex.Location(value="Boston, MA")],
        notes=[
            timdex.Note(
                value=[
                    "Affiches americaines San Domingo: Imprimerie royale du Cap, 1782. "
                    "Nos. 30, 35.",
                ],
                kind="Bibliography",
            ),
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
        ],
        physical_description=(
            "4.5 Cubic Feet (10 manuscript boxes, 1 legal manuscript "
            "box, 1 cassette box); 1.5 Cubic Feet (2 manuscript boxes)"
        ),
        publication_information=[
            "Massachusetts Institute of Technology. Libraries. Department of Distinctive "
            "Collections"
        ],
        related_items=[
            timdex.RelatedItem(
                description=(
                    "A use copy of photographic plates in box 4 can be found in "
                    "the Institute Archives and Special Collections reading room."
                ),
                relationship="Alternate Format",
            ),
            timdex.RelatedItem(
                description=(
                    "Issues of Twilight Zine were separated for library cataloging."
                ),
                relationship="Separated Material",
            ),
            timdex.RelatedItem(
                description="MC-0423 James R. Killian Papers",
            ),
            timdex.RelatedItem(
                description="MC-0416 Karl T. Compton Papers",
            ),
            timdex.RelatedItem(
                description="MC-0029 Carroll Wilson Papers",
            ),
            timdex.RelatedItem(
                description="MC-0060 George Russell Harrison Papers",
            ),
            timdex.RelatedItem(
                description="MC-0351 Margaret Compton Papers",
            ),
            timdex.RelatedItem(
                description=(
                    "AC-0132 Office of the Chancellor; Records of Provost Julius "
                    "A. Stratton, Vice President and Provost Julius A. Stratton, and "
                    "Chancellor Julius A. Stratton"
                )
            ),
            timdex.RelatedItem(
                description=(
                    "AC-0333 Office of the Vice President, Records of Vannevar Bush"
                ),
            ),
            timdex.RelatedItem(
                description=(
                    "The Charles J. Connick and Associates Archives are located "
                    "at the Boston Public Library's Fine Arts Department "
                    "(http://www.bpl.org/research/finearts.htm)."
                ),
            ),
            timdex.RelatedItem(
                description=(
                    "The Charles J. Connick papers, 1901-1949 are located at the "
                    "Smithsonian Archives of American Art "
                    "(http://www.aaa.si.edu/collections/charles-j-connick-papers-7235)."
                ),
            ),
            timdex.RelatedItem(
                description=(
                    "Information on the Charles J. Connick Stained Glass "
                    "Foundation may be found at their website "
                    "(http://www.cjconnick.org/)."
                ),
            ),
        ],
        rights=[
            timdex.Rights(
                description="This collection is open.",
                kind="Conditions Governing Access",
            ),
            timdex.Rights(
                description=(
                    "Access to collections in the Department of Distinctive "
                    "Collections is not authorization to publish. Please see the MIT "
                    "Libraries Permissions Policy for permission information. Copyright "
                    "of some items in this collection may be held by respective "
                    "creators, not by the donor of the collection or MIT."
                ),
                kind="Conditions Governing Use",
            ),
        ],
        subjects=[
            timdex.Subject(value=["Correspondence"]),
            timdex.Subject(value=["Boston, MA"]),
            timdex.Subject(
                value=["Letters (Correspondence)"], kind="Art & Architecture Thesaurus"
            ),
            timdex.Subject(value=["Hutchinson Family"], kind="local"),
            timdex.Subject(value=["Hutchinson, John C."], kind="local"),
            timdex.Subject(
                value=["University of Minnesota"],
                kind="Library of Congress Name Authority File",
            ),
        ],
        summary=[
            "A record of the MIT faculty begins with the minutes of the September 25, "
            "1865, meeting and continues to the present day. Among the topics discussed "
            "at faculty meetings are proposed degree programs, disciplinary actions, "
            "admission and graduation requirements, enrollment and diversity, and issues "
            "concerning student life. This collection includes biographical material in "
            "Killian Award and Edgerton Award announcements and resolutions on the death "
            "of individual faculty members written by faculty peers. Minutes may also "
            "contain reports produced by committees and task forces as their results are "
            "reported and discussed at faculty meetings."
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
            "Title string. Data not enclosed in subelement. Archival materials, "
            "Correspondence. https://archivesspace.mit.edu/repositories/2/resources/6"
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
        identifiers=[
            timdex.Identifier(
                value="Data enclosed in subelement", kind="Collection Identifier"
            )
        ],
        locations=[timdex.Location(value="Data enclosed in subelement")],
        notes=[
            timdex.Note(value=["Data with blank head element"], kind="Bibliography"),
            timdex.Note(value=["Data with no head element"], kind="Bibliography"),
            timdex.Note(
                value=["Data with blank head tag"], kind="Biography or History"
            ),
            timdex.Note(value=["Data with no head tag"], kind="Biography or History"),
            timdex.Note(
                value=["Data with blank head tag"], kind="Scope and Contents Note"
            ),
            timdex.Note(
                value=["Data with no head tag"], kind="Scope and Contents Note"
            ),
        ],
        physical_description="Data not enclosed in subelement",
        publication_information=["Data not enclosed in subelement"],
        related_items=[
            timdex.RelatedItem(
                description="Data with blank head tag",
                relationship="Alternate Format",
            ),
            timdex.RelatedItem(
                description="Data with no head tag",
                relationship="Alternate Format",
            ),
            timdex.RelatedItem(
                description="Data with blank head tag",
                relationship="Separated Material",
            ),
            timdex.RelatedItem(
                description="Data with no head tag",
                relationship="Separated Material",
            ),
            timdex.RelatedItem(
                description="Data with blank head tag",
            ),
            timdex.RelatedItem(
                description="Data with no head tag",
            ),
            timdex.RelatedItem(
                description="List data with blank head tag",
            ),
            timdex.RelatedItem(
                description="List data with no head tag",
            ),
        ],
        subjects=[
            timdex.Subject(value=["Correspondence"]),
            timdex.Subject(value=["Data enclosed in subelement"]),
            timdex.Subject(value=["Subject with blank source attribute"]),
            timdex.Subject(value=["Data enclosed in subelement"]),
            timdex.Subject(
                value=["Data enclosed in subelement with blank source attribute"]
            ),
        ],
        summary=["Data enclosed in subelement"],
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


def test_ead_record_invalid_date_and_date_range_are_omitted(caplog):
    ead_xml_records = parse_xml_records(
        "tests/fixtures/ead/ead_record_attribute_and_subfield_variations.xml"
    )
    output_record = next(Ead("aspace", ead_xml_records))
    assert "abcd" not in [d.value for d in output_record.dates]
    assert "abcd" not in [
        d.range.gte for d in output_record.dates if "gte" in dir(d.range)
    ]
    assert "efgh" not in [
        d.range.lte for d in output_record.dates if "lte" in dir(d.range)
    ]
    assert (
        "Record ID 'repositories/2/resources/6' has invalid values in a date range: "
        "'abcd', 'efgh'"
    ) in caplog.text
    assert (
        "Record ID 'repositories/2/resources/6' has a date that couldn't be parsed: "
        "'abcd'"
    ) in caplog.text


def test_ead_record_correct_identifiers_from_multiple_unitid(caplog):
    ead_xml_records = parse_xml_records(
        "tests/fixtures/ead/ead_record_attribute_and_subfield_variations.xml"
    )
    output_record = next(Ead("aspace", ead_xml_records))
    for identifier in output_record.identifiers:
        assert identifier.value != "unitid-that-should-not-be-identifier"


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
