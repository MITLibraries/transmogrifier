import logging
from typing import Literal

from bs4 import BeautifulSoup

import transmogrifier.models as timdex
from transmogrifier.sources.xml.ead import Ead


def create_ead_source_record_stub(
    header_insert: str = "",
    metadata_insert: str = "",
    parent_element: Literal["archdesc", "did"] = None,  # noqa: RUF013
) -> BeautifulSoup:
    """
    Create source record for unit tests.

    Args:
        header_insert (str): For EAD-formatted XML, the <header> element is used
            in the derivation of 'source_record_id'.
        metadata_insert (str): An string representing a metadata XML element.
        parent_element (Literal["archdesc", "did"]): For EAD-formatted XML,
            all of the information about a collection that is relevant to the
            TIMDEX data model is encapsulated within the <archdesc level="collection">
            element. Metadata will be formatted either as a direct descendant of
            the <archdesc> element or a descendant of the <did> element.

    Note: A source record for "missing" field method tests can be created by
        leaving metadata_insert = "" (the default) and setting parent_element.
    """
    xml_string = """
        <records>
            <record xmlns="http://www.openarchives.org/OAI/2.0/"
                xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
                <header>
                    {header_insert}
                </header>
                <metadata>
                    <ead xmlns="urn:isbn:1-931666-22-9" xmlns:xlink="http://www.w3.org/1999/xlink"
                        xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
                        xsi:schemaLocation="urn:isbn:1-931666-22-9 http://www.loc.gov/ead/ead.xsd">
                        <eadheader countryencoding="iso3166-1" dateencoding="iso8601"
                            findaidstatus="completed"
                            langencoding="iso639-2b"
                            repositoryencoding="iso15511">
                            <eadid countrycode="US" mainagencycode="US-mcm">
                                VC-0002
                            </eadid>
                        </eadheader>
                        {metadata_insert}
                    </ead>
                </metadata>
            </record>
        </records>
    """
    if metadata_insert and parent_element is None:
        message = (
            "Argument 'parent_element' cannot be of NoneType "
            "if 'metadata_insert' is set."
        )
        raise TypeError(message)
    if parent_element == "archdesc":
        _metadata_insert = f"""
            <archdesc level="collection">{metadata_insert}</archdesc>
            """
    elif parent_element == "did":
        _metadata_insert = f"""
            <archdesc level="collection"><did>{metadata_insert}</did></archdesc>
            """

    return BeautifulSoup(
        xml_string.format(header_insert=header_insert, metadata_insert=_metadata_insert),
        "xml",
    )


def test_ead_transform_with_all_fields_transforms_correctly():
    ead_xml_records = Ead.parse_source_file(
        "tests/fixtures/ead/ead_record_all_fields.xml"
    )
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
                range=timdex.DateRange(gte="1905", lte="2012"),
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
        publishers=[
            timdex.Publisher(
                name="Massachusetts Institute of Technology. Libraries. Department of "
                "Distinctive Collections"
            )
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


def test_ead_transform_with_optional_fields_blank_transforms_correctly():
    ead_xml_records = Ead.parse_source_file(
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


def test_ead_transform_with_optional_fields_missing_transforms_correctly():
    ead_xml_records = Ead.parse_source_file(
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


def test_ead_transform_with_attribute_and_subfield_variations_transforms_correctly():
    ead_xml_records = Ead.parse_source_file(
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
                range=timdex.DateRange(gte="1905", lte="2012"),
            ),
            timdex.Date(
                kind="creation",
                range=timdex.DateRange(gte="1905", lte="2012"),
            ),
            timdex.Date(
                note="approximate",
                range=timdex.DateRange(gte="1905", lte="2012"),
            ),
            timdex.Date(
                kind="creation",
                note="approximate",
                range=timdex.DateRange(gte="1905", lte="2012"),
            ),
            timdex.Date(
                range=timdex.DateRange(gte="1953-11-09", lte="1953-11-10"),
            ),
            timdex.Date(value="1969-03-04"),
            timdex.Date(value="2023"),
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
            timdex.Note(value=["Data with blank head tag"], kind="Biography or History"),
            timdex.Note(value=["Data with no head tag"], kind="Biography or History"),
            timdex.Note(
                value=["Data with blank head tag"], kind="Scope and Contents Note"
            ),
            timdex.Note(value=["Data with no head tag"], kind="Scope and Contents Note"),
        ],
        physical_description="Data not enclosed in subelement",
        publishers=[timdex.Publisher(name="Data not enclosed in subelement")],
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


def test_ead_transform_with_missing_archdesc_skips_record():
    ead_xml_records = Ead.parse_source_file(
        "tests/fixtures/ead/ead_record_missing_archdesc.xml"
    )
    output_records = Ead("aspace", ead_xml_records)
    assert len(list(output_records)) == 0
    assert output_records.processed_record_count == 1
    assert output_records.skipped_record_count == 1


def test_ead_transform_with_missing_archdesc_did_skips_record():
    ead_xml_records = Ead.parse_source_file(
        "tests/fixtures/ead/ead_record_missing_archdesc_did.xml"
    )
    output_records = Ead("aspace", ead_xml_records)

    assert len(list(output_records)) == 0
    assert output_records.processed_record_count == 1
    assert output_records.skipped_record_count == 1


def test_ead_transform_with_invalid_date_and_date_range_omits_dates(caplog):
    caplog.set_level(logging.DEBUG)
    ead_xml_records = Ead.parse_source_file(
        "tests/fixtures/ead/ead_record_attribute_and_subfield_variations.xml"
    )
    output_record = next(Ead("aspace", ead_xml_records))

    for date in output_record.dates:
        assert date.value != "undated"
        assert date.value != "1984"
        if date.range is not None:
            assert date.range.gte != "1984"
            assert date.range.lte != "1989"
            assert date.range.gte != "2001"
            assert date.range.lte != "1999"
    assert ("has a date that couldn't be parsed: 'undated'") in caplog.text
    assert ("has a later start date than end date: '2001', '1999'") in caplog.text


def test_get_alternate_titles_success():
    source_record = create_ead_source_record_stub(
        metadata_insert=(
            """
            <unittitle>
                Charles J. Connick Stained Glass
                <emph>
                    Foundation
                    <emph>Collection</emph>
                </emph>
                <num>VC.0002</num>
            </unittitle>
            <unittitle>
                Title 2
                <num>VC.0002</num>
            </unittitle>
            <unittitle>Title 3</unittitle>
            """
        ),
        parent_element="did",
    )
    assert Ead.get_alternate_titles(source_record) == [
        timdex.AlternateTitle(value="Title 2"),
        timdex.AlternateTitle(value="Title 3"),
    ]


def test_get_alternate_titles_transforms_correctly_if_fields_blank():
    source_record = create_ead_source_record_stub(
        metadata_insert=(
            """
            <unittitle>
                Charles J. Connick Stained Glass
                <emph>
                    Foundation
                    <emph>Collection</emph>
                </emph>
                <num>VC.0002</num>
            </unittitle>
            <unittitle></unittitle>
            <unittitle></unittitle>
            """
        ),
        parent_element="did",
    )
    assert Ead.get_alternate_titles(source_record) is None


def test_get_alternate_titles_transforms_correctly_if_fields_missing():
    source_record = create_ead_source_record_stub(
        metadata_insert=(
            """
            <unittitle>
                Charles J. Connick Stained Glass
                <emph>
                    Foundation
                    <emph>Collection</emph>
                </emph>
                <num>VC.0002</num>
            </unittitle>
            """
        ),
        parent_element="did",
    )
    assert Ead.get_alternate_titles(source_record) is None


def test_get_citation_success():
    source_record = create_ead_source_record_stub(
        metadata_insert=(
            "<prefercite><head>Preferred Citation</head><p>"
            "Charles J. Connick Stained Glass Foundation Collection, "
            "VC-0002, box X. Massachusetts Institute of Technology, "
            "Department of Distinctive Collections, Cambridge, Massachusetts."
            "</p></prefercite>"
        ),
        parent_element="archdesc",
    )
    assert Ead.get_citation(source_record) == (
        "Charles J. Connick Stained Glass Foundation Collection, "
        "VC-0002, box X. Massachusetts Institute of Technology, "
        "Department of Distinctive Collections, Cambridge, Massachusetts."
    )


def test_get_citation_transforms_correctly_if_fields_blank():
    source_record = create_ead_source_record_stub(
        metadata_insert=(
            """
            prefercite></prefercite>
            """
        ),
        parent_element="archdesc",
    )
    assert Ead.get_citation(source_record) is None


def test_get_citation_transforms_correctly_if_fields_missing():
    source_record = create_ead_source_record_stub(parent_element="archdesc")
    assert Ead.get_citation(source_record) is None


def test_get_content_type_success():
    source_record = create_ead_source_record_stub(
        metadata_insert=(
            """
            <controlaccess>
                <genreform>
                    <part>Correspondence</part>
                </genreform>
            </controlaccess>
            """
        ),
        parent_element="archdesc",
    )
    assert Ead.get_content_type(source_record) == ["Archival materials", "Correspondence"]


def test_get_content_type_transforms_correctly_if_fields_blank():
    source_record = create_ead_source_record_stub(
        metadata_insert=(
            """
            <controlaccess>
                <genreform></genreform>
            </controlaccess>
            """
        ),
        parent_element="archdesc",
    )
    assert Ead.get_content_type(source_record) == ["Archival materials"]


def test_get_content_type_transforms_correctly_if_fields_missing():
    source_record = create_ead_source_record_stub(
        metadata_insert=(
            """
            <controlaccess></controlaccess>
            """
        ),
        parent_element="archdesc",
    )
    assert Ead.get_content_type(source_record) == ["Archival materials"]


def test_get_contents_success():
    source_record = create_ead_source_record_stub(
        metadata_insert=(
            """
            <arrangement>
                <head>Arrangement</head>
                <p>This collection is organized into ten series: </p>
                <p>Series 1. Charles J. Connick and Connick Studio documents</p>
                <p>Series 2. Charles J. Connick Studio and Associates job information</p>
                <p>Series 3. Charles J. Connick Stained Glass Foundation documents</p>
            </arrangement>
            """
        ),
        parent_element="archdesc",
    )
    assert Ead.get_contents(source_record) == [
        "This collection is organized into ten series:",
        "Series 1. Charles J. Connick and Connick Studio documents",
        "Series 2. Charles J. Connick Studio and Associates job information",
        "Series 3. Charles J. Connick Stained Glass Foundation documents",
    ]


def test_get_contents_transforms_correctly_if_fields_blank():
    source_record = create_ead_source_record_stub(
        metadata_insert=(
            """
            <arrangement></arrangement>
            """
        ),
        parent_element="archdesc",
    )
    assert Ead.get_contents(source_record) is None


def test_get_contents_transforms_correctly_if_fields_missing():
    source_record = create_ead_source_record_stub(parent_element="archdesc")
    assert Ead.get_contents(source_record) is None


def test_get_contributors_success():
    source_record = create_ead_source_record_stub(
        metadata_insert=(
            """
            <origination label="Creator">
                <persname>
                    Author, Best E.
                    <part>( <emph> Best <emph>Ever</emph> </emph> )</part>
                </persname>
            </origination>
            """
        ),
        parent_element="did",
    )
    assert Ead.get_contributors(source_record) == [
        timdex.Contributor(value="Author, Best E. ( Best Ever )", kind="Creator")
    ]


def test_get_contributors_transforms_correctly_if_fields_blank():
    source_record = create_ead_source_record_stub(
        metadata_insert=(
            """
            <origination></origination>
            """
        ),
        parent_element="did",
    )
    assert Ead.get_contributors(source_record) is None


def test_get_contributors_transforms_correctly_if_fields_missing():
    source_record = create_ead_source_record_stub(parent_element="did")
    assert Ead.get_contributors(source_record) is None


def test_get_contributors_transforms_correctly_if_multiple_contributors():
    source_record = create_ead_source_record_stub(
        metadata_insert=(
            """
            <origination label="Creator">
                <persname>
                    Author, Best E.
                    <part>( <emph> Best <emph>Ever</emph> </emph> )</part>
                </persname>
                <persname>
                    Author, Better
                </persname>
            """
        ),
        parent_element="did",
    )
    assert Ead.get_contributors(source_record) == [
        timdex.Contributor(
            value="Author, Best E. ( Best Ever )",
            kind="Creator",
        ),
        timdex.Contributor(
            value="Author, Better",
            kind="Creator",
        ),
    ]


def test_get_contributors_transforms_correctly_with_source_based_identifiers():
    source_record = create_ead_source_record_stub(
        metadata_insert=(
            """
            <origination label="Creator">
                <persname authfilenumber="a001" source="naf">
                    Author, Best E.
                    <part>( <emph> Best <emph>Ever</emph> </emph> )</part>
                </persname>
                <persname authfilenumber="b001" source="viaf">
                    Author, Better
                </persname>
            </origination>
            <origination>
                <famname authfilenumber="c001" source="snac">Fambam</famname>
            </famname>
            """
        ),
        parent_element="did",
    )
    assert Ead.get_contributors(source_record) == [
        timdex.Contributor(
            value="Author, Best E. ( Best Ever )",
            identifier=["https://lccn.loc.gov/a001"],
            kind="Creator",
        ),
        timdex.Contributor(
            value="Author, Better",
            identifier=["http://viaf.org/viaf/b001"],
            kind="Creator",
        ),
        timdex.Contributor(
            value="Fambam", identifier=["https://snaccooperative.org/view/c001"]
        ),
    ]


def test_get_dates_success():
    source_record = create_ead_source_record_stub(
        header_insert=(
            """
            <identifier>oai:mit//repositories/2/resources/1</identifier>
            """
        ),
        metadata_insert=(
            """
            <unitdate certainty="approximate" datechar="creation" normal="1905/2012">
                1905-2012
            </unitdate>
            <unitdate normal="2023-01-01">2023-01-01</unitdate>
            """
        ),
        parent_element="did",
    )
    assert Ead.get_dates(source_record) == [
        timdex.Date(
            kind="creation",
            note="approximate",
            range=timdex.DateRange(gte="1905", lte="2012"),
        ),
        timdex.Date(value="2023-01-01"),
    ]


def test_get_dates_transforms_correctly_if_fields_blank():
    source_record = create_ead_source_record_stub(
        header_insert=(
            """
            <identifier>oai:mit//repositories/2/resources/1</identifier>
            """
        ),
        metadata_insert=(
            """
            <unitdate certainty="approximate" datechar="creation" normal=""></unitdate>
            """
        ),
        parent_element="did",
    )
    assert Ead.get_dates(source_record) is None


def test_get_dates_transforms_correctly_if_fields_missing():
    source_record = create_ead_source_record_stub(
        header_insert=(
            """
            <identifier>oai:mit//repositories/2/resources/1</identifier>
            """
        ),
        parent_element="did",
    )
    assert Ead.get_dates(source_record) is None


def test_get_dates_transforms_correctly_if_date_invalid():
    source_record = create_ead_source_record_stub(
        header_insert=(
            """
            <identifier>oai:mit//repositories/2/resources/1</identifier>
            """
        ),
        metadata_insert=(
            """
            <unitdate certainty="approximate" datechar="creation" normal="">
                INVALID
            </unitdate>
            """
        ),
        parent_element="did",
    )
    assert Ead.get_dates(source_record) is None


def test_get_dates_transforms_correctly_if_normal_attribute_missing():
    source_record = create_ead_source_record_stub(
        header_insert=(
            """
            <identifier>oai:mit//repositories/2/resources/1</identifier>
            """
        ),
        metadata_insert=(
            """
            <unitdate certainty="approximate" datechar="creation">2024</unitdate>
            """
        ),
        parent_element="did",
    )
    assert Ead.get_dates(source_record) is None


def test_get_identifiers_success():
    source_record = create_ead_source_record_stub(
        metadata_insert=(
            """
            <unitid>a001</unitid>
            """
        ),
        parent_element="did",
    )
    assert Ead.get_identifiers(source_record) == [
        timdex.Identifier(value="a001", kind="Collection Identifier")
    ]


def test_get_identifiers_transforms_correctly_if_fields_blank():
    source_record = create_ead_source_record_stub(
        metadata_insert=(
            """
            <unitid></unitid>
            """
        ),
        parent_element="did",
    )
    assert Ead.get_identifiers(source_record) is None


def test_get_identifiers_transforms_correctly_if_fields_missing():
    source_record = create_ead_source_record_stub(
        parent_element="did",
    )
    assert Ead.get_identifiers(source_record) is None


def test_get_identifiers_transforms_correctly_if_type_attribute_invalid():
    source_record = create_ead_source_record_stub(
        metadata_insert=(
            """
            <unitid type="aspace_uri">ignore-me</unitid>
            """
        ),
        parent_element="did",
    )
    assert Ead.get_identifiers(source_record) is None


def test_get_languages_success():
    source_record = create_ead_source_record_stub(
        metadata_insert=(
            """
            <langmaterial>
                <language>English</language>
                ,
                <language>French</language>
                .
            </langmaterial>
            """
        ),
        parent_element="did",
    )
    assert Ead.get_languages(source_record) == ["English", "French"]


def test_get_languages_transforms_correctly_if_fields_blank():
    source_record = create_ead_source_record_stub(
        metadata_insert=(
            """
            <langmaterial></langmaterial>
            """
        ),
        parent_element="did",
    )
    assert Ead.get_languages(source_record) is None


def test_get_languages_transforms_correctly_if_fields_missing():
    source_record = create_ead_source_record_stub(parent_element="did")
    assert Ead.get_languages(source_record) is None


def test_get_locations_success():
    source_record = create_ead_source_record_stub(
        metadata_insert=(
            """
            <controlaccess>
                <geogname>Boston, MA</geogname>
            </controlaccess>
            """
        ),
        parent_element="archdesc",
    )
    assert Ead.get_locations(source_record) == [timdex.Location(value="Boston, MA")]


def test_get_locations_transforms_correctly_if_fields_blank():
    source_record = create_ead_source_record_stub(
        metadata_insert=(
            """
            <controlaccess>
                <geogname></geogname>
            </controlaccess>
            """
        ),
        parent_element="archdesc",
    )
    assert Ead.get_locations(source_record) is None


def test_get_locations_transforms_correctly_if_fields_missing():
    source_record = create_ead_source_record_stub(parent_element="archdesc")
    assert Ead.get_locations(source_record) is None


def test_get_notes_success():
    source_record = create_ead_source_record_stub(
        metadata_insert=(
            """
            <bibliography>
                <head>Bibliography</head>
                <bibref>
                    <title>
                        <part>Affiches americaines</part>
                    </title>
                    San Domingo:
                    <emph>Imprimerie</emph>
                    royale du Cap, 1782. Nos. 30, 35.
                </bibref>
            </bibliography>
            """
        ),
        parent_element="archdesc",
    )
    assert Ead.get_notes(source_record) == [
        timdex.Note(
            value=[
                (
                    "Affiches americaines San Domingo: "
                    "Imprimerie royale du Cap, 1782. Nos. 30, 35."
                )
            ],
            kind="Bibliography",
        )
    ]


def test_get_notes_transforms_correctly_if_fields_blank():
    source_record = create_ead_source_record_stub(
        metadata_insert=(
            """
            <bibliography></bibliography>
            <bioghist></bioghist>
            <scopecontent></scopecontent>
            """
        ),
        parent_element="archdesc",
    )
    assert Ead.get_notes(source_record) is None


def test_get_notes_transforms_correctly_if_fields_missing():
    source_record = create_ead_source_record_stub(parent_element="archdesc")
    assert Ead.get_notes(source_record) is None


def test_get_notes_transforms_correctly_with_multiple_kinds():
    source_record = create_ead_source_record_stub(
        metadata_insert=(
            """
            <bibliography>
                <head>Bibliography</head>
                <bibref>
                    <title>
                        <part>Affiches americaines</part>
                    </title>
                    San Domingo:
                    <emph>Imprimerie</emph>
                    royale du Cap, 1782. Nos. 30, 35.
                </bibref>
            </bibliography>
            <bioghist>
                <head>Biographical Note</head>
                <p>
            """
            "Charles J. Connick (1875-1945) was an American "
            "<emph>stained</emph> glass artist whose work may be found "
            "in cities all across the United States."
            """
                </p>
                <p>Connick founded his own studio in 1912 in Boston.</p>
            </bioghist>
            """
        ),
        parent_element="archdesc",
    )
    assert Ead.get_notes(source_record) == [
        timdex.Note(
            value=[
                (
                    "Affiches americaines San Domingo: "
                    "Imprimerie royale du Cap, 1782. Nos. 30, 35."
                )
            ],
            kind="Bibliography",
        ),
        timdex.Note(
            value=[
                (
                    "Charles J. Connick (1875-1945) was an American "
                    "stained glass artist whose work may be found "
                    "in cities all across the United States."
                ),
                "Connick founded his own studio in 1912 in Boston.",
            ],
            kind="Biographical Note",
        ),
    ]


def test_get_notes_transforms_correctly_if_head_missing():
    source_record = create_ead_source_record_stub(
        metadata_insert=(
            """
            <bibliography>
                <bibref>
                    <title>
                        <part>Affiches americaines</part>
                    </title>
                    San Domingo:
                    <emph>Imprimerie</emph>
                    royale du Cap, 1782. Nos. 30, 35.
                </bibref>
            </bibliography>
            """
        ),
        parent_element="archdesc",
    )
    assert Ead.get_notes(source_record) == [
        timdex.Note(
            value=[
                (
                    "Affiches americaines San Domingo: "
                    "Imprimerie royale du Cap, 1782. Nos. 30, 35."
                )
            ],
            kind="Bibliography",
        )
    ]


def test_get_physical_description_success():
    source_record = create_ead_source_record_stub(
        metadata_insert=(
            """
            <physdesc>
                <extent>4.5 Cubic Feet</extent>
                <extent>
                    (10 manuscript boxes, 1 legal manuscript box, 1 cassette box)
                </extent>
            </physdesc>
            """
        ),
        parent_element="did",
    )
    assert Ead.get_physical_description(source_record) == (
        "4.5 Cubic Feet (10 manuscript boxes, 1 legal manuscript box, 1 cassette box)"
    )


def test_get_physical_description_transforms_correctly_if_fields_blank():
    source_record = create_ead_source_record_stub(
        metadata_insert=(
            """
            <physdesc></physdesc>
            """
        ),
        parent_element="did",
    )
    assert Ead.get_physical_description(source_record) is None


def test_get_physical_description_transforms_correctly_if_fields_missing():
    source_record = create_ead_source_record_stub(parent_element="did")
    assert Ead.get_physical_description(source_record) is None


def test_get_physical_description_transforms_correctly_if_multiple_physdesc():
    source_record = create_ead_source_record_stub(
        metadata_insert=(
            """
            <physdesc>
                <extent>4.5 Cubic Feet</extent>
                <extent>
                    (10 manuscript boxes, 1 legal manuscript box, 1 cassette box)
                </extent>
            </physdesc>
            <physdesc>
                <extent>1.5 Cubic Feet</extent>
                <extent>(2 manuscript boxes)</extent>
            </physdesc>
            """
        ),
        parent_element="did",
    )
    assert Ead.get_physical_description(source_record) == (
        "4.5 Cubic Feet (10 manuscript boxes, 1 legal manuscript box, 1 cassette box); "
        "1.5 Cubic Feet (2 manuscript boxes)"
    )


def test_get_publishers_success():
    source_record = create_ead_source_record_stub(
        metadata_insert=(
            """
            <repository>
                <corpname>
                    Massachusetts
                    <emph>Institute</emph>
                    of Technology. Libraries. Department of Distinctive Collections
                </corpname>
            </repository>
            """
        ),
        parent_element="did",
    )
    assert Ead.get_publishers(source_record) == [
        timdex.Publisher(
            name=(
                "Massachusetts Institute of Technology. Libraries. "
                "Department of Distinctive Collections"
            )
        )
    ]


def test_get_publishers_transforms_correctly_if_fields_blank():
    source_record = create_ead_source_record_stub(
        metadata_insert=(
            """
            <repository></repository>
            """
        ),
        parent_element="did",
    )
    assert Ead.get_publishers(source_record) is None


def test_get_publishers_transforms_correctly_if_fields_missing():
    source_record = create_ead_source_record_stub(parent_element="did")
    assert Ead.get_publishers(source_record) is None


def test_get_summary_success():
    source_record = create_ead_source_record_stub(
        metadata_insert=(
            "<abstract>"
            "A record of the <emph>MIT</emph> faculty begins with "
            "the minutes of the September 25, 1865, "
            "meeting and continues to the present day."
            "</abstract>"
        ),
        parent_element="did",
    )
    assert Ead.get_summary(source_record) == [
        (
            "A record of the MIT faculty begins with "
            "the minutes of the September 25, 1865, "
            "meeting and continues to the present day."
        )
    ]


def test_get_summary_transforms_correctly_if_fields_blank():
    source_record = create_ead_source_record_stub(
        metadata_insert=(
            """
            <abstract></abstract>
            """
        ),
        parent_element="did",
    )
    assert Ead.get_summary(source_record) is None


def test_get_summary_transforms_correctly_if_fields_missing():
    source_record = create_ead_source_record_stub(parent_element="did")
    assert Ead.get_summary(source_record) is None


def test_get_main_titles_success():
    source_record = create_ead_source_record_stub(
        metadata_insert=(
            """
            <unittitle>
                Charles J. Connick Stained Glass
                <emph>
                    Foundation
                    <emph>Collection</emph>
                </emph>
                <num>VC.0002</num>
            </unittitle>
            <unittitle>
                Title 2
                <num>VC.0002</num>
            </unittitle>
            <unittitle>Title 3</unittitle>
            """
        ),
        parent_element="did",
    )
    assert Ead.get_main_titles(source_record) == [
        "Charles J. Connick Stained Glass Foundation Collection",
        "Title 2",
        "Title 3",
    ]


def test_get_main_titles_transforms_correctly_if_fields_blank():
    source_record = create_ead_source_record_stub(
        metadata_insert=(
            """
            <unittitle></unittitle>
            """
        ),
        parent_element="did",
    )
    assert Ead.get_main_titles(source_record) == []


def test_get_main_titles_transforms_correctly_if_fields_missing():
    source_record = create_ead_source_record_stub(parent_element="did")
    assert Ead.get_main_titles(source_record) == []
