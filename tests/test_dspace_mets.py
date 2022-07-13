import transmogrifier.models as timdex
from transmogrifier.helpers import parse_xml_records
from transmogrifier.sources.dspace_mets import DspaceMets


def test_dspace_mets_transform_with_missing_optional_fields_transforms_correctly():
    dspace_xml_records = parse_xml_records(
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
    )


def test_dspace_mets_transform_with_blank_optional_fields_transforms_correctly():
    dspace_xml_records = parse_xml_records(
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
    )


def test_dspace_mets_transform_with_all_fields_transforms_correctly():
    dspace_xml_records = parse_xml_records(
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
            timdex.AlternateTitle(
                kind="alternative", value="A Slightly Different Title"
            )
        ],
        citation='Tatsumi, Yuki. "Magneto-thermal Transport and Machine '
        'Learning-assisted Investigation of Magnetic Materials." Massachusetts '
        "Institute of Technology © 2022.",
        content_type=["Thesis"],
        contributors=[
            timdex.Contributor(
                value="Checkelsky, Joseph",
                kind="advisor",
            ),
            timdex.Contributor(
                value="Tatsumi, Yuki",
                kind="author",
            ),
            timdex.Contributor(
                value="Massachusetts Institute of Technology. Department of Physics",
                kind="department",
            ),
            timdex.Contributor(
                value="Smith, Susie Q.",
                kind="Contributor role not specified",
            ),
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
        publication_information=["Massachusetts Institute of Technology"],
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
