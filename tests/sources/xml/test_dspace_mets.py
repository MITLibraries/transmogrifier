from bs4 import BeautifulSoup

import transmogrifier.models as timdex
from transmogrifier.sources.xml.dspace_mets import DspaceMets


def create_dspace_mets_source_record_stub(xml_insert: str = "") -> BeautifulSoup:
    xml_string = f"""
        <records>
         <record xmlns="http://www.openarchives.org/OAI/2.0/"
         xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
          <header>
            <identifier>abc123</identifier>
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
                {xml_insert}
                </mods:mods>
              </xmlData>
             </mdWrap>
            </dmdSec>
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
    assert next(output_records) == timdex.TimdexRecord(
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
    assert next(output_records) == timdex.TimdexRecord(
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
    assert next(output_records) == timdex.TimdexRecord(
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
    assert next(output_records) == timdex.TimdexRecord(
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
        """
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
        '<titles><title titleType="AlternativeTitle"></title></titles>'
    )
    assert DspaceMets.get_alternate_titles(source_record) is None


def test_get_alternate_titles_transforms_correctly_if_fields_missing():
    source_record = create_dspace_mets_source_record_stub()
    assert DspaceMets.get_alternate_titles(source_record) is None


def test_get_alternate_titles_multiple_titles_success():

    source_record = create_dspace_mets_source_record_stub(
        """
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
    source_record = create_dspace_mets_source_record_stub(xml_string)
    assert DspaceMets.get_citation(source_record) == (
        'Tatsumi, Yuki. "Magneto-thermal Transport and Machine Learning-assisted '
        'Investigation of Magnetic Materials." Massachusetts Institute of Technology '
        "© 2022."
    )


def test_get_citation_transforms_correctly_if_fields_blank():
    source_record = create_dspace_mets_source_record_stub(
        '<mods:identifier type="citation"></mods:identifier>'
    )
    assert DspaceMets.get_citation(source_record) is None


def test_get_citation_transforms_correctly_if_fields_missing():
    source_record = create_dspace_mets_source_record_stub()
    assert DspaceMets.get_citation(source_record) is None


def test_get_content_type_success():
    source_record = create_dspace_mets_source_record_stub(
        "<mods:genre>Thesis</mods:genre>"
    )
    assert DspaceMets.get_content_type(source_record) == ["Thesis"]


def test_get_content_type_transforms_correctly_if_fields_blank():
    source_record = create_dspace_mets_source_record_stub("<mods:genre />")
    assert DspaceMets.get_content_type(source_record) is None


def test_get_content_type_transforms_correctly_if_fields_missing():
    source_record = create_dspace_mets_source_record_stub()
    assert DspaceMets.get_content_type(source_record) is None
