from bs4 import BeautifulSoup

import transmogrifier.models as timdex
from transmogrifier.sources.xml.dspace_mets import DspaceMets


def create_dspace_mets_source_record_stub(
    dmdsec_insert: str = "", filesec_insert: str = ""
) -> BeautifulSoup:
    xml_string = f"""
        <records>
         <record xmlns="http://www.openarchives.org/OAI/2.0/"
         xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
          <header>
            <identifier>oai:dspace:abc123</identifier>
          <header>
          <metadata>
           <mets xmlns="http://www.loc.gov/METS/"
                xmlns:doc="http://www.lyncode.com/xoai"
                xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
                xmlns:xlink="http://www.w3.org/1999/xlink"
                xsi:schemaLocation="http://www.loc.gov/METS/
            <dmdSec ID="DMD_1721.1_142832">
             <mdWrap MDTYPE="MODS">
              <xmlData xmlns:mods="http://www.loc.gov/mods/v3"
               xsi:schemaLocation="http://www.loc.gov/mods/v3
               http://www.loc.gov/standards/mods/v3/mods-3-1.xsd">
                <mods:mods>
                {dmdsec_insert}
                </mods:mods>
              </xmlData>
             </mdWrap>
            </dmdSec>
            <fileSec>
            {filesec_insert}
            </fileSec>
           </mets>
          </metadata>
         </record>
        </records>
        """
    return BeautifulSoup(xml_string, "xml")


def test_dspace_mets_transform_with_all_fields_transforms_correctly():
    dspace_xml_records = DspaceMets.parse_source_file(
        "tests/fixtures/dspace/dspace_mets_record_all_fields.xml"
    )
    output_records = DspaceMets("dspace", dspace_xml_records)
    timdex_record = output_records.transform(next(output_records.source_records))
    assert timdex_record == timdex.TimdexRecord(
        source="DSpace@MIT",
        source_link="https://dspace.mit.edu/handle/1721.1/142832",
        timdex_record_id="dspace:1721.1-142832",
        title="Magneto-thermal Transport and Machine Learning-assisted Investigation "
        "of Magnetic Materials",
        alternate_titles=[
            timdex.AlternateTitle(kind="alternative", value="A Slightly Different Title")
        ],
        citation='Tatsumi, Yuki. "Magneto-thermal Transport and Machine '
        'Learning-assisted Investigation of Magnetic Materials." Massachusetts '
        "Institute of Technology © 2022.",
        content_type=["Thesis"],
        contributors=[
            timdex.Contributor(value="Checkelsky, Joseph", kind="advisor"),
            timdex.Contributor(value="Tatsumi, Yuki", kind="author"),
            timdex.Contributor(
                value="Massachusetts Institute of Technology. Department of Physics",
                kind="department",
            ),
            timdex.Contributor(value="Smith, Susie Q.", kind="Not specified"),
        ],
        dates=[timdex.Date(kind="Publication date", value="2021-09")],
        file_formats=["application/pdf"],
        format="electronic resource",
        identifiers=[
            timdex.Identifier(kind="uri", value="https://hdl.handle.net/1721.1/142832")
        ],
        languages=["en_US"],
        links=[
            timdex.Link(
                kind="Digital object URL",
                text="Digital object URL",
                url="https://hdl.handle.net/1721.1/142832",
            )
        ],
        numbering="MIT-CSAIL-TR-2018-016",
        publishers=[timdex.Publisher(name="Massachusetts Institute of Technology")],
        related_items=[
            timdex.RelatedItem(description="Nature Communications", relationship="host")
        ],
        rights=[
            timdex.Rights(
                description="In Copyright - Educational Use Permitted",
                kind="useAndReproduction",
            )
        ],
        subjects=[
            timdex.Subject(
                kind="Subject scheme not provided",
                value=["Metallurgy and Materials Science"],
            ),
        ],
        summary=[
            "Heat is carried by different types quasiparticles in crystals, including "
            "phonons, charge carriers, and magnetic excitations. In most materials, "
            "thermal transport can be understood as the flow of phonons and charge "
            "carriers; magnetic heat flow is less well-studied and less well "
            "understood.\r \rRecently, the concept of the flat band, with a vanishing "
            "dispersion, has gained importance. Especially in electronic systems, many "
            "theories and experiments have proven that some structures such as kagome "
            "or honeycomb lattices hosts such flat bands with non-trivial topology. "
            "Even though a number of theories suggest that such dispersionless mode "
            "exist in magnonic bands under the framework of the Heisenberg spin model, "
            "few experiments indicate its existence. Not limited to these flat band "
            "effects, magnetic insulators can assume a variety of nontrivial "
            "topologies such as magnetic skyrmions. In this thesis, I investigate the "
            "highly frustrated magnetic system Y0.5Ca0.5BaCo4O7, where the kagome "
            "lattice could potentially lead to nontrivial thermal transport originated "
            "from its flat band. While we do not observe signatures of the flat band "
            "in thermal conductivity, the observed anomalous Hall effect in electrical "
            "transport and spin glass-like behavior suggest a complex "
            "magnetization-transport mechanism.\r\rMotivated by the rapid advancement "
            "of artificial inteligence, the application of machine learning into "
            "materials exploration is recently investigated. Using a graphical "
            "representation of crystallines orginally suggested in Crystal Graphical "
            "Convolutional Neural Network (CGCNN), we developed the ML-asssited method "
            "to explore magnetic compounds. Our machine learning model can, so far, "
            "distiguish ferromagnet or antiferromagnet systems with over 70% accuracy "
            "based only on structual/elemental information. Prospects of studying more "
            "complex magnets are described."
        ],
    )


def test_dspace_mets_transform_with_blank_optional_fields_transforms_correctly():
    dspace_xml_records = DspaceMets.parse_source_file(
        "tests/fixtures/dspace/dspace_mets_record_optional_fields_blank.xml"
    )
    output_records = DspaceMets("dspace", dspace_xml_records)
    timdex_record = output_records.transform(next(output_records.source_records))
    assert timdex_record == timdex.TimdexRecord(
        source="DSpace@MIT",
        source_link="https://dspace.mit.edu/handle/1721.1/142832",
        timdex_record_id="dspace:1721.1-142832",
        title="Title not provided",
        citation="Title not provided. https://dspace.mit.edu/handle/1721.1/142832",
        format="electronic resource",
        content_type=["Not specified"],
    )


def test_dspace_mets_transform_with_missing_optional_fields_transforms_correctly():
    dspace_xml_records = DspaceMets.parse_source_file(
        "tests/fixtures/dspace/dspace_mets_record_optional_fields_missing.xml"
    )
    output_records = DspaceMets("dspace", dspace_xml_records)
    timdex_record = output_records.transform(next(output_records.source_records))
    assert timdex_record == timdex.TimdexRecord(
        source="DSpace@MIT",
        source_link="https://dspace.mit.edu/handle/1721.1/142832",
        timdex_record_id="dspace:1721.1-142832",
        title="Title not provided",
        citation="Title not provided. https://dspace.mit.edu/handle/1721.1/142832",
        format="electronic resource",
        content_type=["Not specified"],
    )


def test_dspace_mets_with_attribute_and_subfield_variations_transforms_correctly():
    dspace_xml_records = DspaceMets.parse_source_file(
        "tests/fixtures/dspace/dspace_mets_record_attribute_and_subfield_variations.xml"
    )
    output_records = DspaceMets("dspace", dspace_xml_records)
    timdex_record = output_records.transform(next(output_records.source_records))
    assert timdex_record == timdex.TimdexRecord(
        source="DSpace@MIT",
        source_link="https://dspace.mit.edu/handle/1721.1/142832",
        timdex_record_id="dspace:1721.1-142832",
        title="Title with Blank Type",
        citation="Title with Blank Type. 2021-09. Thesis. "
        "https://dspace.mit.edu/handle/1721.1/142832",
        alternate_titles=[timdex.AlternateTitle(value="Second Title with Blank Type")],
        content_type=["Thesis"],
        contributors=[
            timdex.Contributor(value="One, Author", kind="Not specified"),
            timdex.Contributor(value="Two, Author", kind="Not specified"),
            timdex.Contributor(value="Three, Author", kind="Not specified"),
        ],
        dates=[timdex.Date(kind="Publication date", value="2021-09")],
        file_formats=["application/pdf"],
        format="electronic resource",
        identifiers=[
            timdex.Identifier(kind="Not specified", value="ID-no-type"),
            timdex.Identifier(kind="Not specified", value="ID-blank-type"),
            timdex.Identifier(kind="uri", value="https://link-to-item"),
        ],
        links=[
            timdex.Link(
                kind="Digital object URL",
                text="Digital object URL",
                url="https://link-to-item",
            )
        ],
        related_items=[
            timdex.RelatedItem(
                description="Related item no type", relationship="Not specified"
            ),
            timdex.RelatedItem(
                description="Related item blank type", relationship="Not specified"
            ),
        ],
        rights=[
            timdex.Rights(description="Access condition no type"),
            timdex.Rights(description="Access condition blank type"),
        ],
    )


def test_get_alternate_titles_success():
    source_record = create_dspace_mets_source_record_stub(
        dmdsec_insert="""
        <mods:titleInfo>
         <mods:title type="alternative">A Slightly Different Title</mods:title>
        </mods:titleInfo>
        """
    )
    assert DspaceMets.get_alternate_titles(source_record) == [
        timdex.AlternateTitle(value="A Slightly Different Title", kind="alternative")
    ]


def test_get_alternate_titles_transforms_correctly_if_fields_blank():
    source_record = create_dspace_mets_source_record_stub(
        dmdsec_insert='<titles><title titleType="AlternativeTitle"></title></titles>'
    )
    assert DspaceMets.get_alternate_titles(source_record) is None


def test_get_alternate_titles_transforms_correctly_if_fields_missing():
    source_record = create_dspace_mets_source_record_stub()
    assert DspaceMets.get_alternate_titles(source_record) is None


def test_get_alternate_titles_multiple_titles_success():

    source_record = create_dspace_mets_source_record_stub(
        dmdsec_insert="""
        <mods:titleInfo>
         <mods:title>Title 1</mods:title>"
        </mods:titleInfo>
        <mods:titleInfo>
         <mods:title>Title 2</mods:title>
        </mods:titleInfo>
        <mods:titleInfo>
         <mods:title>Title 3</mods:title>
        </mods:titleInfo>
        """
    )
    assert DspaceMets.get_alternate_titles(source_record) == [
        timdex.AlternateTitle(value="Title 2"),
        timdex.AlternateTitle(value="Title 3"),
    ]


def test_get_citation_success():
    xml_string = (
        '<mods:identifier type="citation">Tatsumi, Yuki. "Magneto-thermal '
        'Transport and Machine Learning-assisted Investigation of Magnetic Materials." '
        "Massachusetts Institute of Technology © 2022.</mods:identifier>"
    )
    source_record = create_dspace_mets_source_record_stub(dmdsec_insert=xml_string)
    assert DspaceMets.get_citation(source_record) == (
        'Tatsumi, Yuki. "Magneto-thermal Transport and Machine Learning-assisted '
        'Investigation of Magnetic Materials." Massachusetts Institute of Technology '
        "© 2022."
    )


def test_get_citation_transforms_correctly_if_fields_blank():
    source_record = create_dspace_mets_source_record_stub(
        dmdsec_insert='<mods:identifier type="citation"></mods:identifier>'
    )
    assert DspaceMets.get_citation(source_record) is None


def test_get_citation_transforms_correctly_if_fields_missing():
    source_record = create_dspace_mets_source_record_stub()
    assert DspaceMets.get_citation(source_record) is None


def test_get_content_type_success():
    source_record = create_dspace_mets_source_record_stub(
        dmdsec_insert="<mods:genre>Thesis</mods:genre>"
    )
    assert DspaceMets.get_content_type(source_record) == ["Thesis"]


def test_get_content_type_transforms_correctly_if_fields_blank():
    source_record = create_dspace_mets_source_record_stub(dmdsec_insert="<mods:genre />")
    assert DspaceMets.get_content_type(source_record) is None


def test_get_content_type_transforms_correctly_if_fields_missing():
    source_record = create_dspace_mets_source_record_stub()
    assert DspaceMets.get_content_type(source_record) is None


def test_get_contribtuors_success():
    source_record = create_dspace_mets_source_record_stub(
        dmdsec_insert="""
        <mods:name>
         <mods:role>
          <mods:roleTerm type="text">advisor</mods:roleTerm>
         </mods:role>
         <mods:namePart>Checkelsky, Joseph</mods:namePart>
        </mods:name>
        <mods:name>
         <mods:role>
          <mods:roleTerm type="text">author</mods:roleTerm>
         </mods:role>
         <mods:namePart>Tatsumi, Yuki</mods:namePart>
        </mods:name>
        <mods:name>
         <mods:role>
           <mods:roleTerm type="text">department</mods:roleTerm>
         </mods:role>
         <mods:namePart>Massachusetts Institute of Technology. Department</mods:namePart>
        </mods:name>
        <mods:name>
         <mods:namePart>Smith, Susie Q.</mods:namePart>
        </mods:name>
        """
    )
    assert DspaceMets.get_contributors(source_record) == [
        timdex.Contributor(
            value="Checkelsky, Joseph",
            kind="advisor",
        ),
        timdex.Contributor(
            value="Tatsumi, Yuki",
            kind="author",
        ),
        timdex.Contributor(
            value="Massachusetts Institute of Technology. Department",
            kind="department",
        ),
        timdex.Contributor(
            value="Smith, Susie Q.",
            kind="Not specified",
        ),
    ]


def test_get_contributors_transforms_correctly_if_fields_blank():
    source_record = create_dspace_mets_source_record_stub(
        dmdsec_insert="<mods:name><mods:namePart /></mods:name>"
    )
    assert DspaceMets.get_contributors(source_record) is None


def test_get_contributors_transforms_correctly_if_fields_missing():
    source_record = create_dspace_mets_source_record_stub()
    assert DspaceMets.get_contributors(source_record) is None


def test_get_dates_success():
    source_record = create_dspace_mets_source_record_stub(
        dmdsec_insert="""
        <mods:originInfo>
         <mods:dateIssued encoding="iso8601">2021-09</mods:dateIssued>
        </mods:originInfo>
        """
    )
    assert DspaceMets.get_dates(source_record) == [
        timdex.Date(kind="Publication date", value="2021-09")
    ]


def test_get_dates_transforms_correctly_if_fields_blank():
    source_record = create_dspace_mets_source_record_stub(
        dmdsec_insert="<mods:originInfo><mods:dateIssued /></mods:originInfo>"
    )
    assert DspaceMets.get_dates(source_record) is None


def test_get_dates_transforms_correctly_if_fields_missing():
    source_record = create_dspace_mets_source_record_stub()
    assert DspaceMets.get_dates(source_record) is None


def test_get_file_formats_success():
    source_record = create_dspace_mets_source_record_stub(
        filesec_insert="""
        <fileGrp USE="ORIGINAL">
         <file ID="BITSTREAM_ORIGINAL_1721.1_142832_1"
        MIMETYPE="application/pdf">
          <FLocat xlink:type="simple" LOCTYPE="URL"
          xlink:href="https://dspace.mit.edu/bitstream/1721.1/142832/1/1.pdf"/>
         </file>
        </fileGrp>
        <fileGrp USE="TEXT">
          <file ID="BITSTREAM_TEXT_1721.1_142832_2" MIMETYPE="text/plain">
          <FLocat xlink:type="simple" LOCTYPE="URL"
          xlink:href="https://dspace.mit.edu/bitstream/1721.1/142832/2/1.pdf.txt"/>
         </file>
        </fileGrp>
        """
    )
    assert DspaceMets.get_file_formats(source_record) == ["application/pdf"]


def test_get_file_formats_transforms_correctly_if_fields_blank():
    source_record = create_dspace_mets_source_record_stub(
        '<fileGrp USE="ORIGINAL"><file MIMETYPE="" /></<fileGrp>'
    )
    assert DspaceMets.get_file_formats(source_record) is None


def test_get_file_formats_transforms_correctly_if_fields_missing():
    source_record = create_dspace_mets_source_record_stub()
    assert DspaceMets.get_file_formats(source_record) is None


def test_get_format_success():
    assert DspaceMets.get_format() == "electronic resource"


def test_get_identifiers_success():
    source_record = create_dspace_mets_source_record_stub(
        dmdsec_insert="""
        <mods:identifier type="uri">https://hdl.handle.net/1721.1/142832</mods:identifier>
        """
    )
    assert DspaceMets.get_identifiers(source_record) == [
        timdex.Identifier(value="https://hdl.handle.net/1721.1/142832", kind="uri"),
    ]


def test_get_identifiers_transforms_correctly_if_fields_blank():
    source_record = create_dspace_mets_source_record_stub(
        dmdsec_insert="<mods:identifier />"
    )
    assert DspaceMets.get_identifiers(source_record) is None


def test_get_identifers_transforms_correctly_if_fields_missing():
    source_record = create_dspace_mets_source_record_stub()
    assert DspaceMets.get_identifiers(source_record) is None


def test_get_languages_success():
    source_record = create_dspace_mets_source_record_stub(
        dmdsec_insert="""
        <mods:language>
         <mods:languageTerm authority="rfc3066">en_US</mods:languageTerm>
        </mods:language>
        """
    )
    assert DspaceMets.get_languages(source_record) == ["en_US"]


def test_get_languages_transforms_correctly_if_fields_blank():
    source_record = create_dspace_mets_source_record_stub(
        dmdsec_insert="<mods:language><mods:languageTerm /></mods:language>"
    )
    assert DspaceMets.get_languages(source_record) is None


def test_get_languages_transforms_correctly_if_fields_missing():
    source_record = create_dspace_mets_source_record_stub()
    assert DspaceMets.get_languages(source_record) is None


def test_get_links_success():
    source_record = create_dspace_mets_source_record_stub(
        dmdsec_insert="""
        <mods:identifier type="uri">https://hdl.handle.net/1721.1/142832</mods:identifier>
        """
    )
    assert DspaceMets.get_links(source_record) == [
        timdex.Link(
            url="https://hdl.handle.net/1721.1/142832",
            kind="Digital object URL",
            text="Digital object URL",
        ),
    ]


def test_get_links_transforms_correctly_if_fields_blank():
    source_record = create_dspace_mets_source_record_stub(
        dmdsec_insert="<mods:identifier />"
    )
    assert DspaceMets.get_links(source_record) is None


def test_get_links_transforms_correctly_if_fields_missing():
    source_record = create_dspace_mets_source_record_stub()
    assert DspaceMets.get_links(source_record) is None


def test_get_numbering_success():
    source_record = create_dspace_mets_source_record_stub(
        dmdsec_insert="<mods:relatedItem "
        'type="series">MIT-CSAIL-TR-2018-016</mods:relatedItem>'
    )
    assert DspaceMets.get_numbering(source_record) == "MIT-CSAIL-TR-2018-016"


def test_get_numbering_transforms_correctly_if_fields_blank():
    source_record = create_dspace_mets_source_record_stub(
        dmdsec_insert='<mods:relatedItem type="series" />'
    )
    assert DspaceMets.get_numbering(source_record) is None


def test_get_numbering_transforms_correctly_if_fields_missing():
    source_record = create_dspace_mets_source_record_stub()
    assert DspaceMets.get_numbering(source_record) is None


def test_get_publishers_success():
    source_record = create_dspace_mets_source_record_stub(
        dmdsec_insert="""
        <mods:originInfo>
         <mods:publisher>Massachusetts Institute of Technology</mods:publisher>
        </mods:originInfo>
        """
    )
    assert DspaceMets.get_publishers(source_record) == [
        timdex.Publisher(name="Massachusetts Institute of Technology"),
    ]


def test_get_publishers_transforms_correctly_if_fields_blank():
    source_record = create_dspace_mets_source_record_stub(
        dmdsec_insert="<mods:originInfo><mods:publisher /></mods:originInfo>"
    )
    assert DspaceMets.get_publishers(source_record) is None


def test_get_publishers_transforms_correctly_if_fields_missing():
    source_record = create_dspace_mets_source_record_stub()
    assert DspaceMets.get_publishers(source_record) is None


def test_get_related_items_success():
    source_record = create_dspace_mets_source_record_stub(
        dmdsec_insert="""
        <mods:relatedItem type="host">Nature Communications</mods:relatedItem>
        """
    )
    assert DspaceMets.get_related_items(source_record) == [
        timdex.RelatedItem(description="Nature Communications", relationship="host"),
    ]


def test_get_related_items_transforms_correctly_if_fields_blank():
    source_record = create_dspace_mets_source_record_stub(
        dmdsec_insert='<mods:relatedItem type="host" />'
    )
    assert DspaceMets.get_related_items(source_record) is None


def test_get_related_items_transforms_correctly_if_fields_missing():
    source_record = create_dspace_mets_source_record_stub()
    assert DspaceMets.get_related_items(source_record) is None


def test_get_rights_items_success():
    dmdsec_insert = (
        '<mods:accessCondition type="useAndReproduction">'
        "In Copyright - Educational Use Permitted</mods:accessCondition>"
    )
    source_record = create_dspace_mets_source_record_stub(dmdsec_insert)
    assert DspaceMets.get_rights(source_record) == [
        timdex.Rights(
            description="In Copyright - Educational Use Permitted",
            kind="useAndReproduction",
        ),
    ]


def test_get_rights_transforms_correctly_if_fields_blank():
    source_record = create_dspace_mets_source_record_stub(
        dmdsec_insert="<mods:accessCondition />"
    )
    assert DspaceMets.get_rights(source_record) is None


def test_get_rights_transforms_correctly_if_fields_missing():
    source_record = create_dspace_mets_source_record_stub()
    assert DspaceMets.get_rights(source_record) is None


def test_get_subjects_items_success():
    source_record = create_dspace_mets_source_record_stub(
        dmdsec_insert="""
        <mods:subject>
         <mods:topic>Metallurgy and Materials Science</mods:topic>
        </mods:subject>
        """
    )
    assert DspaceMets.get_subjects(source_record) == [
        timdex.Subject(
            value=["Metallurgy and Materials Science"],
            kind="Subject scheme not provided",
        ),
    ]


def test_get_subjects_transforms_correctly_if_fields_blank():
    source_record = create_dspace_mets_source_record_stub(
        dmdsec_insert="<mods:subject><mods:topic /></mods:subject>"
    )
    assert DspaceMets.get_subjects(source_record) is None


def test_get_subjects_transforms_correctly_if_fields_missing():
    source_record = create_dspace_mets_source_record_stub()
    assert DspaceMets.get_subjects(source_record) is None


def test_get_summary_items_success():
    source_record = create_dspace_mets_source_record_stub(
        dmdsec_insert="<mods:abstract>Heat is carried by different.</mods:abstract>"
    )
    assert DspaceMets.get_summary(source_record) == ["Heat is carried by different."]


def test_get_summary_transforms_correctly_if_fields_blank():
    source_record = create_dspace_mets_source_record_stub(
        dmdsec_insert="<mods:abstract />"
    )
    assert DspaceMets.get_summary(source_record) is None


def test_get_summary_transforms_correctly_if_fields_missing():
    source_record = create_dspace_mets_source_record_stub()
    assert DspaceMets.get_summary(source_record) is None
