from bs4 import BeautifulSoup

import transmogrifier.models as timdex
from transmogrifier.sources.xml.dspace_dim import DspaceDim


def create_dspace_dim_source_record_stub(xml_insert: str = "") -> BeautifulSoup:
    xml_string = f"""
        <records>
         <record xmlns="http://www.openarchives.org/OAI/2.0/"
         xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
          <header>
           <identifier>oai:darchive.mblwhoilibrary.org:1912/2641</identifier>
           <datestamp>2020-01-28T19:30:01Z</datestamp>
           <setSpec>com_1912_3</setSpec>
           <setSpec>col_1912_534</setSpec>
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


def test_dspace_dim_transform_with_all_fields_transforms_correctly():
    source_records = DspaceDim.parse_source_file(
        "tests/fixtures/dspace/dspace_dim_record_all_fields.xml"
    )
    output_records = DspaceDim("cool-repo", source_records)
    timdex_record = output_records.transform(next(output_records.source_records))
    assert timdex_record == timdex.TimdexRecord(
        citation="Journal of Geophysical Research: Solid Earth 121 (2016): 5859-5879",
        source="A Cool Repository",
        source_link="https://example.com/1912/2641",
        timdex_record_id="cool-repo:1912-2641",
        title=(
            "Time lapse movie of meiosis I in a living spermatocyte from the crane fly, "
            "Nephrotoma suturalis, viewed with polarized light microscopy"
        ),
        alternate_titles=[
            timdex.AlternateTitle(value="An Alternative Title", kind="alternative"),
        ],
        content_type=["Moving Image", "Dataset"],
        contents=["Chapter 1"],
        contributors=[
            timdex.Contributor(
                value="Jamerson, James",
                kind="Creator",
            ),
            timdex.Contributor(
                value="LaFountain, James R.",
                kind="author",
            ),
            timdex.Contributor(
                value="Oldenbourg, Rudolf",
                kind="author",
            ),
        ],
        dates=[
            timdex.Date(kind="accessioned", value="2009-01-08T16:24:37Z"),
            timdex.Date(kind="available", value="2009-01-08T16:24:37Z"),
            timdex.Date(kind="Publication date", value="2002-11"),
            timdex.Date(kind="coverage", note="1201-01-01 - 1965-12-21"),
            timdex.Date(
                kind="coverage",
                range=timdex.DateRange(gte="1201-01-01", lte="1965-12-21"),
            ),
        ],
        file_formats=[
            "application/msword",
            "image/tiff",
            "video/quicktime",
        ],
        format="electronic resource",
        funding_information=[
            timdex.Funder(
                funder_name="NSF Grant Numbers: OCE-1029305, OCE-1029411, OCE-1249353",
            )
        ],
        identifiers=[
            timdex.Identifier(value="https://hdl.handle.net/1912/2641", kind="uri")
        ],
        languages=["en_US"],
        links=[
            timdex.Link(
                url="https://hdl.handle.net/1912/2641",
                kind="Digital object URL",
                text="Digital object URL",
            )
        ],
        locations=[timdex.Location(value="Central equatorial Pacific Ocean")],
        notes=[
            timdex.Note(
                value=[
                    (
                        "Author Posting. © The Author(s), 2008. This is the author's "
                        "version of the work. It is posted here by permission of John "
                        "Wiley  Sons for personal use, not for redistribution. The "
                        "definitive version was published in Journal of Field Robotics "
                        "25 (2008): 861-879, doi:10.1002/rob.20250."
                    )
                ],
            ),
            timdex.Note(value=["2026-01"], kind="embargo"),
        ],
        publishers=[timdex.Publisher(name="Woods Hole Oceanographic Institution")],
        related_items=[
            timdex.RelatedItem(
                description="A low resolution version of this movie was published as "
                "supplemental material to: Rieder, C. L. and A. Khodjakov. Mitosis "
                "through the microscope: advances in seeing inside live dividing "
                "cells. Science 300 (2003): 91-96, doi: 10.1126/science.1082177",
                relationship="Not specified",
            ),
            timdex.RelatedItem(
                description="International Association of Aquatic and Marine Science "
                "Libraries and Information Centers (38th : 2012: Anchorage, Alaska)",
                relationship="ispartofseries",
            ),
            timdex.RelatedItem(
                uri="https://doi.org/10.1002/2016JB013228",
                relationship="Not specified",
            ),
        ],
        rights=[
            timdex.Rights(
                description="Attribution-NonCommercial-NoDerivatives 4.0 International",
            ),
            timdex.Rights(
                uri="http://creativecommons.org/licenses/by-nc-nd/4.0/",
            ),
            timdex.Rights(description="CC-BY-NC 4.0", kind="license"),
        ],
        subjects=[
            timdex.Subject(
                value=["Spermatocyte", "Microtubules", "Kinetochore microtubules"],
                kind="lcsh",
            ),
            timdex.Subject(
                value=["Polarized light microscopy", "LC-PolScope"],
                kind="Subject scheme not provided",
            ),
        ],
        summary=[
            (
                "The events of meiosis I in a living spermatocyte obtained from the "
                "testis of a crane-fly larva are recorded in this time-lapse sequence "
                "beginning at diakinesis through telophase to the near completion of "
                "cytokinesis following meiosis I."
            )
        ],
    )


def test_dspace_dim_transform_with_attribute_variations_transforms_correctly():
    source_records = DspaceDim.parse_source_file(
        "tests/fixtures/dspace/dspace_dim_record_attribute_variations.xml"
    )
    output_records = DspaceDim("cool-repo", source_records)
    timdex_record = output_records.transform(next(output_records.source_records))
    assert timdex_record == timdex.TimdexRecord(
        citation="Title with Blank Qualifier. https://example.com/1912/2641",
        source="A Cool Repository",
        source_link="https://example.com/1912/2641",
        timdex_record_id="cool-repo:1912-2641",
        title=("Title with Blank Qualifier"),
        alternate_titles=[
            timdex.AlternateTitle(value="Additional Title with No Qualifier")
        ],
        content_type=["Not specified"],
        contributors=[
            timdex.Contributor(kind="Not specified", value="Contributor, No Qualifier"),
            timdex.Contributor(
                kind="Not specified", value="Contributor, Blank Qualifier"
            ),
        ],
        dates=[
            timdex.Date(value="2020-01-01"),
            timdex.Date(value="2020-01-02"),
        ],
        format="electronic resource",
        identifiers=[
            timdex.Identifier(kind="Not specified", value="Identifier no qualifier"),
            timdex.Identifier(kind="Not specified", value="Identifier blank qualifier"),
        ],
        notes=[
            timdex.Note(value=["Description no qualifier"]),
            timdex.Note(value=["Description blank qualifier"]),
        ],
        related_items=[
            timdex.RelatedItem(
                description="Related item no qualifier", relationship="Not specified"
            ),
            timdex.RelatedItem(
                description="Related item blank qualifier", relationship="Not specified"
            ),
        ],
        rights=[
            timdex.Rights(description="Right no qualifier"),
            timdex.Rights(description="Right blank qualifier"),
        ],
        subjects=[
            timdex.Subject(
                value=["Subject no qualifier", "Subject blank qualifier"],
                kind="Subject scheme not provided",
            ),
        ],
    )


def test_dspace_dim_transform_with_optional_fields_blank_transforms_correctly():
    source_records = DspaceDim.parse_source_file(
        "tests/fixtures/dspace/dspace_dim_record_optional_fields_blank.xml"
    )
    output_records = DspaceDim("cool-repo", source_records)
    timdex_record = output_records.transform(next(output_records.source_records))
    assert timdex_record == timdex.TimdexRecord(
        source="A Cool Repository",
        source_link="https://example.com/1912/2641",
        timdex_record_id="cool-repo:1912-2641",
        title="Title not provided",
        citation="Title not provided. https://example.com/1912/2641",
        format="electronic resource",
        content_type=["Not specified"],
    )


def test_dspace_dim_transform_with_optional_fields_missing_transforms_correctly():
    source_records = DspaceDim.parse_source_file(
        "tests/fixtures/dspace/dspace_dim_record_optional_fields_missing.xml"
    )
    output_records = DspaceDim("cool-repo", source_records)
    timdex_record = output_records.transform(next(output_records.source_records))
    assert timdex_record == timdex.TimdexRecord(
        source="A Cool Repository",
        source_link="https://example.com/1912/2641",
        timdex_record_id="cool-repo:1912-2641",
        title="Title not provided",
        citation="Title not provided. https://example.com/1912/2641",
        format="electronic resource",
        content_type=["Not specified"],
    )


def test_get_alternate_titles_success():
    source_record = create_dspace_dim_source_record_stub(
        """
        <dim:field mdschema="dc" element="title"
        qualifier="alternative" lang="en">An Alternative Title</dim:field>
        """
    )
    assert DspaceDim.get_alternate_titles(source_record) == [
        timdex.AlternateTitle(value="An Alternative Title", kind="alternative")
    ]


def test_get_alternate_titles_transforms_correctly_if_fields_blank():
    source_record = create_dspace_dim_source_record_stub(
        '<dim:field mdschema="dc" element="title" qualifier="alternative" />'
    )
    assert DspaceDim.get_alternate_titles(source_record) is None


def test_get_alternate_titles_transforms_correctly_if_fields_missing():
    source_record = create_dspace_dim_source_record_stub()
    assert DspaceDim.get_alternate_titles(source_record) is None


def test_get_alternate_titles_multiple_titles_success():

    source_record = create_dspace_dim_source_record_stub(
        """
        <dim:field mdschema="dc" element="title">Title 1</dim:field>
        <dim:field mdschema="dc" element="title">Title 2</dim:field>
        <dim:field mdschema="dc" element="title">Title 3</dim:field>
        """
    )
    assert DspaceDim.get_alternate_titles(source_record) == [
        timdex.AlternateTitle(value="Title 2"),
        timdex.AlternateTitle(value="Title 3"),
    ]


def test_get_citation_success():
    source_record = create_dspace_dim_source_record_stub(
        """
        <dim:field mdschema="dc" element="identifier"
        qualifier="citation"
        >Journal of Geophysical Research: Solid Earth 121 (2016): 5859-5879</dim:field>
        """
    )
    assert (
        DspaceDim.get_citation(source_record)
        == "Journal of Geophysical Research: Solid Earth 121 (2016): 5859-5879"
    )


def test_get_citation_transforms_correctly_if_fields_blank():
    source_record = create_dspace_dim_source_record_stub(
        '<dim:field mdschema="dc" element="identifier" qualifier="citation" />'
    )
    assert DspaceDim.get_citation(source_record) is None


def test_get_citation_transforms_correctly_if_fields_missing():
    source_record = create_dspace_dim_source_record_stub()
    assert DspaceDim.get_citation(source_record) is None


def test_get_content_type_success():
    source_record = create_dspace_dim_source_record_stub(
        """
        <dim:field mdschema="dc" element="type">Moving Image</dim:field>
        <dim:field mdschema="dc" element="type">Dataset</dim:field>
        """
    )
    assert DspaceDim.get_content_type(source_record) == [
        "Moving Image",
        "Dataset",
    ]


def test_get_content_type_transforms_correctly_if_fields_blank():
    source_record = create_dspace_dim_source_record_stub(
        '<dim:field mdschema="dc" element="type" />'
    )
    assert DspaceDim.get_content_type(source_record) is None


def test_get_content_type_transforms_correctly_if_fields_missing():
    source_record = create_dspace_dim_source_record_stub()
    assert DspaceDim.get_content_type(source_record) is None


def test_get_contents_success():
    source_record = create_dspace_dim_source_record_stub(
        """
        <dim:field mdschema="dc" element="description" qualifier="tableofcontents"
        >Chapter 1</dim:field>
        """
    )
    assert DspaceDim.get_contents(source_record) == ["Chapter 1"]


def test_get_contents_transforms_correctly_if_fields_blank():
    source_record = create_dspace_dim_source_record_stub(
        '<dim:field mdschema="dc" element="description" qualifier="tableofcontents" />'
    )
    assert DspaceDim.get_contents(source_record) is None


def test_get_contents_transforms_correctly_if_fields_missing():
    source_record = create_dspace_dim_source_record_stub()
    assert DspaceDim.get_contents(source_record) is None


def test_get_contributors_success():
    source_record = create_dspace_dim_source_record_stub(
        """
        <dim:field mdschema="dc" element="contributor"
        qualifier="author">LaFountain, James R.</dim:field>
        <dim:field mdschema="dc" element="contributor"
        qualifier="author">Oldenbourg, Rudolf</dim:field>
        <dim:field mdschema="dc" element="creator">Jamerson, James</dim:field>
        """
    )
    assert DspaceDim.get_contributors(source_record) == [
        timdex.Contributor(value="Jamerson, James", kind="Creator"),
        timdex.Contributor(
            value="LaFountain, James R.",
            kind="author",
        ),
        timdex.Contributor(
            value="Oldenbourg, Rudolf",
            kind="author",
        ),
    ]


def test_get_contributors_transforms_correctly_if_fields_blank():
    source_record = create_dspace_dim_source_record_stub(
        """
        <dim:field mdschema="dc" element="contributor" qualifier="author" />
        <dim:field mdschema="dc" element="creator" />
        """
    )
    assert DspaceDim.get_contributors(source_record) is None


def test_get_contributors_transforms_correctly_if_fields_missing():
    source_record = create_dspace_dim_source_record_stub()
    assert DspaceDim.get_contributors(source_record) is None


def test_get_dates_success():
    source_record = create_dspace_dim_source_record_stub(
        """
        <dim:field mdschema="dc" element="coverage"
        qualifier="temporal">1201-01-01 - 1965-12-21</dim:field>
        <dim:field mdschema="dc" element="coverage"
        qualifier="temporal">1201-01-01/1965-12-21</dim:field>
        <dim:field mdschema="dc" element="date"
        qualifier="accessioned">2009-01-08T16:24:37Z</dim:field>
        <dim:field mdschema="dc" element="date"
        qualifier="available">2009-01-08T16:24:37Z</dim:field>
        <dim:field mdschema="dc" element="date" qualifier="issued">2002-11</dim:field>
        """
    )
    assert DspaceDim.get_dates(source_record) == [
        timdex.Date(kind="accessioned", value="2009-01-08T16:24:37Z"),
        timdex.Date(kind="available", value="2009-01-08T16:24:37Z"),
        timdex.Date(kind="Publication date", value="2002-11"),
        timdex.Date(
            kind="coverage",
            note="1201-01-01 - 1965-12-21",
        ),
        timdex.Date(
            kind="coverage",
            range=timdex.DateRange(gte="1201-01-01", lte="1965-12-21"),
        ),
    ]


def test_get_dates_transforms_correctly_if_fields_blank():
    source_record = create_dspace_dim_source_record_stub(
        """
        <dim:field mdschema="dc" element="coverage" qualifier="temporal" />
        <dim:field mdschema="dc" element="date" qualifier="available" />
        """
    )
    assert DspaceDim.get_dates(source_record) is None


def test_get_dates_transforms_correctly_if_fields_missing():
    source_record = create_dspace_dim_source_record_stub()
    assert DspaceDim.get_dates(source_record) is None


def test_get_file_formats_success():
    source_record = create_dspace_dim_source_record_stub(
        """
        <dim:field mdschema="dc" element="format"
        qualifier="mimetype">application/msword</dim:field>
        <dim:field mdschema="dc" element="format"
        qualifier="mimetype">image/tiff</dim:field>
        <dim:field mdschema="dc" element="format"
        qualifier="mimetype">video/quicktime</dim:field>
        """
    )
    assert DspaceDim.get_file_formats(source_record) == [
        "application/msword",
        "image/tiff",
        "video/quicktime",
    ]


def test_get_file_formats_transforms_correctly_if_fields_blank():
    source_record = create_dspace_dim_source_record_stub(
        '<dim:field mdschema="dc" element="format" qualifier="mimetype" />'
    )
    assert DspaceDim.get_file_formats(source_record) is None


def test_get_file_formats_transforms_correctly_if_fields_missing():
    source_record = create_dspace_dim_source_record_stub()
    assert DspaceDim.get_file_formats(source_record) is None


def test_get_format_success():
    assert DspaceDim.get_format() == "electronic resource"


def test_get_funding_information_success():
    source_record = create_dspace_dim_source_record_stub(
        """
        <dim:field mdschema="dc" element="description" qualifier="sponsorship"
        >NSF Grant Numbers: OCE-1029305, OCE-1029411, OCE-1249353</dim:field>
        """
    )
    assert DspaceDim.get_funding_information(source_record) == [
        timdex.Funder(
            funder_name="NSF Grant Numbers: OCE-1029305, OCE-1029411, OCE-1249353",
        )
    ]


def test_get_funding_information_transforms_correctly_if_fields_blank():
    source_record = create_dspace_dim_source_record_stub(
        '<dim:field mdschema="dc" element="description" qualifier="sponsorship" />'
    )
    assert DspaceDim.get_funding_information(source_record) is None


def test_get_funding_information_transforms_correctly_if_fields_missing():
    source_record = create_dspace_dim_source_record_stub()
    assert DspaceDim.get_funding_information(source_record) is None


def test_get_identifiers_success():
    source_record = create_dspace_dim_source_record_stub(
        """
        <dim:field mdschema="dc" element="identifier" qualifier="uri">https://hdl.handle.net/1912/2641</dim:field>
        """
    )
    assert DspaceDim.get_identifiers(source_record) == [
        timdex.Identifier(value="https://hdl.handle.net/1912/2641", kind="uri")
    ]


def test_get_identifiers_transforms_correctly_if_fields_blank():
    source_record = create_dspace_dim_source_record_stub(
        '<dim:field mdschema="dc" element="identifier" qualifier="uri" />'
    )
    assert DspaceDim.get_identifiers(source_record) is None


def test_get_identifiers_transforms_correctly_if_fields_missing():
    source_record = create_dspace_dim_source_record_stub()
    assert DspaceDim.get_identifiers(source_record) is None


def test_get_languages_success():
    source_record = create_dspace_dim_source_record_stub(
        """
        <dim:field mdschema="dc" element="language" qualifier="iso">en_US</dim:field>
        """
    )
    assert DspaceDim.get_languages(source_record) == ["en_US"]


def test_get_languages_transforms_correctly_if_fields_blank():
    source_record = create_dspace_dim_source_record_stub(
        '<dim:field mdschema="dc" element="language" qualifier="iso" />'
    )
    assert DspaceDim.get_languages(source_record) is None


def test_get_languages_transforms_correctly_if_fields_missing():
    source_record = create_dspace_dim_source_record_stub()
    assert DspaceDim.get_languages(source_record) is None


def test_get_links_success():
    source_record = create_dspace_dim_source_record_stub(
        """
        <dim:field mdschema="dc" element="identifier"
        qualifier="uri">https://hdl.handle.net/1912/2641</dim:field>
        """
    )
    assert DspaceDim.get_links(source_record) == [
        timdex.Link(
            url="https://hdl.handle.net/1912/2641",
            kind="Digital object URL",
            text="Digital object URL",
        )
    ]


def test_get_links_transforms_correctly_if_fields_blank():
    source_record = create_dspace_dim_source_record_stub(
        '<dim:field mdschema="dc" element="identifier" qualifier="uri" />'
    )
    assert DspaceDim.get_links(source_record) is None


def test_get_links_transforms_correctly_if_fields_missing():
    source_record = create_dspace_dim_source_record_stub()
    assert DspaceDim.get_links(source_record) is None


def test_get_locations_success():
    source_record = create_dspace_dim_source_record_stub(
        """
        <dim:field mdschema="dc" element="coverage"
        qualifier="spatial">Central equatorial Pacific Ocean</dim:field>
        """
    )
    assert DspaceDim.get_locations(source_record) == [
        timdex.Location(value="Central equatorial Pacific Ocean")
    ]


def test_get_locations_transforms_correctly_if_fields_blank():
    source_record = create_dspace_dim_source_record_stub(
        '<dim:field mdschema="dc" element="coverage" qualifier="spatial" />'
    )
    assert DspaceDim.get_locations(source_record) is None


def test_get_locations_transforms_correctly_if_fields_missing():
    source_record = create_dspace_dim_source_record_stub()
    assert DspaceDim.get_locations(source_record) is None


def test_get_notes_success():
    source_record = create_dspace_dim_source_record_stub(
        """
        <dim:field mdschema="dc"
        element="description">Author Posting. © The Author(s), 2008.</dim:field>
        <dim:field mdschema="dc" element="description"
        qualifier="embargo">2026-01</dim:field>
        """
    )
    assert DspaceDim.get_notes(source_record) == [
        timdex.Note(value=["Author Posting. © The Author(s), 2008."]),
        timdex.Note(value=["2026-01"], kind="embargo"),
    ]


def test_get_notes_transforms_correctly_if_fields_blank():
    source_record = create_dspace_dim_source_record_stub(
        '<dim:field mdschema="dc" element="description" />'
    )
    assert DspaceDim.get_notes(source_record) is None


def test_get_notes_transforms_correctly_if_fields_missing():
    source_record = create_dspace_dim_source_record_stub()
    assert DspaceDim.get_notes(source_record) is None


def test_get_publishers_success():
    source_record = create_dspace_dim_source_record_stub(
        """
        <dim:field mdschema="dc"
        element="publisher">Woods Hole Oceanographic Institution</dim:field>
        """
    )
    assert DspaceDim.get_publishers(source_record) == [
        timdex.Publisher(name="Woods Hole Oceanographic Institution")
    ]


def test_get_publishers_transforms_correctly_if_fields_blank():
    source_record = create_dspace_dim_source_record_stub(
        '<dim:field mdschema="dc" element="publisher" />'
    )
    assert DspaceDim.get_publishers(source_record) is None


def test_get_publishers_transforms_correctly_if_fields_missing():
    source_record = create_dspace_dim_source_record_stub()
    assert DspaceDim.get_publishers(source_record) is None


def test_get_related_items_success():
    source_record = create_dspace_dim_source_record_stub(
        """
        <dim:field mdschema="dc" element="relation"
        >A low resolution version of this movie was published.</dim:field>
        <dim:field mdschema="dc" element="relation" qualifier="ispartofseries"
        >International Association of Aquatic and Marine Science</dim:field>
        <dim:field mdschema="dc" element="relation" qualifier="uri"
        >https://doi.org/10.1002/2016JB013228</dim:field>
        """
    )
    assert DspaceDim.get_related_items(source_record) == [
        timdex.RelatedItem(
            description="A low resolution version of this movie was published.",
            relationship="Not specified",
        ),
        timdex.RelatedItem(
            description="International Association of Aquatic and Marine Science",
            relationship="ispartofseries",
        ),
        timdex.RelatedItem(
            relationship="Not specified",
            uri="https://doi.org/10.1002/2016JB013228",
        ),
    ]


def test_get_related_items_transforms_correctly_if_fields_blank():
    source_record = create_dspace_dim_source_record_stub(
        '<dim:field mdschema="dc" element="relation" />'
    )
    assert DspaceDim.get_related_items(source_record) is None


def test_get_related_items_transforms_correctly_if_fields_missing():
    source_record = create_dspace_dim_source_record_stub()
    assert DspaceDim.get_related_items(source_record) is None


def test_get_rights_success():
    source_record = create_dspace_dim_source_record_stub(
        """
        <dim:field mdschema="dc" element="rights"
        >Attribution-NonCommercial-NoDerivatives 4.0 International</dim:field>
        <dim:field mdschema="dc" element="rights"
        qualifier="uri">http://creativecommons.org/licenses/by-nc-nd/4.0/</dim:field>
        <dim:field mdschema="dc" element="rights"
        qualifier="license">CC-BY-NC 4.0</dim:field>
        """
    )
    assert DspaceDim.get_rights(source_record) == [
        timdex.Rights(
            description="Attribution-NonCommercial-NoDerivatives 4.0 International"
        ),
        timdex.Rights(uri="http://creativecommons.org/licenses/by-nc-nd/4.0/"),
        timdex.Rights(description="CC-BY-NC 4.0", kind="license", uri=None),
    ]


def test_get_rights_transforms_correctly_if_fields_blank():
    source_record = create_dspace_dim_source_record_stub(
        '<dim:field mdschema="dc" element="rights" />'
    )
    assert DspaceDim.get_rights(source_record) is None


def test_get_rights_transforms_correctly_if_fields_missing():
    source_record = create_dspace_dim_source_record_stub()
    assert DspaceDim.get_rights(source_record) is None


def test_get_subjects_success():
    source_record = create_dspace_dim_source_record_stub(
        """
        <dim:field mdschema="dc" element="subject"
        qualifier="lcsh">Spermatocyte</dim:field>
        <dim:field mdschema="dc" element="subject"
        qualifier="lcsh">Microtubules</dim:field>
        <dim:field mdschema="dc" element="subject"
        qualifier="lcsh">Kinetochore microtubules</dim:field>
        <dim:field mdschema="dc" element="subject">Polarized light microscopy</dim:field>
        <dim:field mdschema="dc" element="subject">LC-PolScope</dim:field>
        """
    )
    assert DspaceDim.get_subjects(source_record) == [
        timdex.Subject(
            value=["Spermatocyte", "Microtubules", "Kinetochore microtubules"],
            kind="lcsh",
        ),
        timdex.Subject(
            value=["Polarized light microscopy", "LC-PolScope"],
            kind="Subject scheme not provided",
        ),
    ]


def test_get_subjects_transforms_correctly_if_fields_blank():
    source_record = create_dspace_dim_source_record_stub(
        '<dim:field mdschema="dc" element="subject" />'
    )
    assert DspaceDim.get_subjects(source_record) is None


def test_get_subjects_transforms_correctly_if_fields_missing():
    source_record = create_dspace_dim_source_record_stub()
    assert DspaceDim.get_subjects(source_record) is None


def test_get_summary_success():
    source_record = create_dspace_dim_source_record_stub(
        """
        <dim:field mdschema="dc" element="description"
        qualifier="abstract">The events of meiosis I in a living.</dim:field>
        """
    )
    assert DspaceDim.get_summary(source_record) == [
        "The events of meiosis I in a living."
    ]


def test_get_summary_transforms_correctly_if_fields_blank():
    source_record = create_dspace_dim_source_record_stub(
        '<dim:field mdschema="dc" element="description" qualifier="abstract" />'
    )
    assert DspaceDim.get_summary(source_record) is None


def test_get_summary_transforms_correctly_if_fields_missing():
    source_record = create_dspace_dim_source_record_stub()
    assert DspaceDim.get_summary(source_record) is None
