import transmogrifier.models as timdex
from transmogrifier.helpers import parse_xml_records
from transmogrifier.sources.marc import Marc


def test_marc_record_all_fields_transform_correctly():
    marc_xml_records = parse_xml_records(
        "tests/fixtures/marc/marc_record_all_fields.xml"
    )
    output_records = Marc("alma", marc_xml_records)
    assert next(output_records) == timdex.TimdexRecord(
        source="MIT Alma",
        source_link=(
            "https://mit.primo.exlibrisgroup.com/discovery/fulldisplay?vid="
            "01MIT_INST:MIT&docid=alma990027185640106761"
        ),
        timdex_record_id="alma:990027185640106761",
        title="Célébration : 10 siècles de musique de noël",
        alternate_titles=[
            timdex.AlternateTitle(
                value="Main Entry Date 1 Date 2", kind="Preferred Title"
            ),
            timdex.AlternateTitle(
                value="Uniform Date 1 Date 2", kind="Preferred Title"
            ),
            timdex.AlternateTitle(
                value="Varying Form Of Title 1", kind="Varying Form of Title"
            ),
            timdex.AlternateTitle(
                value="Varying Form Of Title 2", kind="Varying Form of Title"
            ),
            timdex.AlternateTitle(
                value="Added Entry 1 Part 1 Part 2",
                kind="Preferred Title",
            ),
            timdex.AlternateTitle(
                value="Added Entry 2 Part 1 Part 2",
                kind="Preferred Title",
            ),
            timdex.AlternateTitle(
                value="Added Entry 1 Part 1 Part 2",
                kind="Uncontrolled Related/Analytical Title",
            ),
            timdex.AlternateTitle(
                value="Added Entry 2 Part 1 Part 2",
                kind="Uncontrolled Related/Analytical Title",
            ),
        ],
        call_numbers=[
            "MA123.4",
            "LC Call Number 2",
            "LC Call Number 3",
            "123.45",
            "Dewey Call Number 2",
            "Dewey Call Number 3",
        ],
        citation=(
            "Célébration : 10 siècles de musique de noël. Language material. "
            "https://mit.primo.exlibrisgroup.com/discovery/fulldisplay?vid="
            "01MIT_INST:MIT&docid=alma990027185640106761"
        ),
        content_type=["Language material"],
        contents=[
            (
                "Die Seejungfrau : sinfonische Dichtung : (Fantasie nach Hans Christian "
                "Andersen) (44:29)"
            ),
            "Sinfonietta, op. 23 (22:05)",
            "Wesendonck-Lieder WWV 91",
            "Richard Wagner",
            "(20:45)",
            "Rückert-Lieder",
            "Gustav Mahler",
            "(19:33)",
        ],
        contributors=[
            timdex.Contributor(
                value="Tran, Phong",
                kind="composer",
            ),
            timdex.Contributor(
                value="Tran, Phong",
                kind="performer",
            ),
            timdex.Contributor(
                value="Ceeys (Musical group)",
                kind="composer",
            ),
            timdex.Contributor(
                value="Ceeys (Musical group)",
                kind="performer",
            ),
            timdex.Contributor(
                value="Theory of Cryptography Conference 2008 : New York, N.Y.)",
                kind="Not specified",
            ),
            timdex.Contributor(
                value="Binelli, Daniel",
                kind="arranger of music",
            ),
            timdex.Contributor(
                value="Binelli, Daniel",
                kind="composer",
            ),
            timdex.Contributor(
                value="Binelli, Daniel",
                kind="instrumentalist",
            ),
            timdex.Contributor(
                value="Isaac, Eduardo Elias",
                kind="arranger of music",
            ),
            timdex.Contributor(
                value="Isaac, Eduardo Elias",
                kind="instrumentalist",
            ),
            timdex.Contributor(
                value="Divinerinnen (Musical group)",
                kind="arranger of music",
            ),
            timdex.Contributor(
                value="Divinerinnen (Musical group)",
                kind="instrumentalist",
            ),
            timdex.Contributor(
                value="Motörhead (Musical group)",
                kind="arranger of music",
            ),
            timdex.Contributor(
                value="Motörhead (Musical group)",
                kind="instrumentalist",
            ),
            timdex.Contributor(
                value="Bayreuther Festspiele",
                kind="Orchester",
            ),
            timdex.Contributor(
                value="Bayreuther Festspiele",
                kind="instrumentalist",
            ),
            timdex.Contributor(
                value="Bayreuther Festspiele",
                kind="Chor",
            ),
            timdex.Contributor(
                value="Bayreuther Festspiele",
                kind="singer",
            ),
        ],
        edition="9th ed. / Nick Ray ... [et al.]. Unabridged.",
        literary_form="Nonfiction",
        subjects=[
            timdex.Subject(
                value=[
                    "Renoir, Jean, 1894-1979 (DLC)n  79018203 Bibliography. "
                    "(DLC)sh 99001362"
                ],
                kind="Personal Name",
            ),
            timdex.Subject(
                value=["Renoir, Jean, 1894-1979. (OCoLC)fst00031256"],
                kind="Personal Name",
            ),
            timdex.Subject(
                value=[
                    "United States. Federal Bureau of Investigation (DLC)n  78095617 "
                    "History. (DLC)sh 99005024"
                ],
                kind="Corporate Name",
            ),
            timdex.Subject(
                value=[
                    "United States. Federal Bureau of Investigation. (OCoLC)fst00528882"
                ],
                kind="Corporate Name",
            ),
            timdex.Subject(
                value=[
                    "Musique vocale sacrée (CaQQLa)201-0004748 France "
                    "(CaQQLa)201-0452039 500-1400. (CaQQLa)201-0373671"
                ],
                kind="Topical Term",
            ),
            timdex.Subject(value=["Sacred songs, Unaccompanied"], kind="Topical Term"),
            timdex.Subject(
                value=["Great Plains (DLC)sh 85056998 Climate. (DLC)sh 00007747"],
                kind="Geographic Name",
            ),
            timdex.Subject(
                value=["Great Plains. (OCoLC)fst01240567"], kind="Geographic Name"
            ),
        ],
        summary=[
            "This safety guide provides guidance on meeting the requirements for the "
            "establishment of radiation protection programs (RPPs) for the transport of "
            "radioactive material, to optimize radiation protection in order to meet the "
            "requirements for radiation protection that underlie the Regulations for the "
            "Safe Transport of Radioactive Material. It covers general aspects of "
            "meeting the requirements for radiation protection, but does not cover "
            "criticality safety or other possible hazardous properties of radioactive "
            "material. The annexes of this guide include examples of RPPs, relevant "
            "excerpts from the Transport Regulations, examples of total dose per "
            "transport index handled, a checklist for road transport, specific "
            "segregation distances and emergency instructions for vehicle operators."
            "--Publisher's description.",
            "It is only since the bel canto era in the 19th century that the tenor voice "
            "really took off as a leading character in operatic roles, often playing the "
            "heroic figure against a love-interest soprano and a villain baritone. This "
            "collection of some of opera's most iconic arias takes us from the dark "
            "emotional crises of Leoncavallo's Pagliacci and Puccini's Tosca, to the "
            "seductive Rodolfo in La Bohème and Donizetti's show-stopping hich Cs in La "
            "Fille du régiment. Tenor showpieces that are so famous they have taken on "
            "a life of their own include 'Nessun dorma', made immortal by The Three "
            "Tenors at the 1990 World Cup.",
        ],
    )


def test_marc_record_attribute_and_subfield_variations_transforms_correctly():
    marc_xml_records = parse_xml_records(
        "tests/fixtures/marc/marc_record_attribute_and_subfield_variations.xml",
    )
    output_records = Marc("alma", marc_xml_records)
    assert next(output_records) == timdex.TimdexRecord(
        source="MIT Alma",
        source_link=(
            "https://mit.primo.exlibrisgroup.com/discovery/fulldisplay?vid="
            "01MIT_INST:MIT&docid=alma990027185640106761"
        ),
        timdex_record_id="alma:990027185640106761",
        title="a b f g k n p s",
        alternate_titles=[
            timdex.AlternateTitle(
                value="a d f g h k l m n o p r s t",
                kind="Preferred Title",
            ),
            timdex.AlternateTitle(
                value="a d f g h k l m n o p r s", kind="Preferred Title"
            ),
            timdex.AlternateTitle(
                value="a b f g h i n p", kind="Varying Form of Title"
            ),
            timdex.AlternateTitle(
                value="a d f g h i k l m n o p r s t",
                kind="Preferred Title",
            ),
            timdex.AlternateTitle(
                value="a n p",
                kind="Uncontrolled Related/Analytical Title",
            ),
        ],
        call_numbers=["a", "a"],
        citation=(
            "a b f g k n p s. Manuscript language material. "
            "https://mit.primo.exlibrisgroup.com/discovery/"
            "fulldisplay?vid=01MIT_INST:MIT&docid=alma990027185640106761"
        ),
        content_type=["Manuscript language material"],
        contents=["a", "g", "r", "t"],
        contributors=[
            timdex.Contributor(
                value="a b c q",
                kind="e",
            ),
            timdex.Contributor(
                value="a b c",
                kind="e",
            ),
            timdex.Contributor(
                value="a c d f g j q",
                kind="e",
            ),
        ],
        edition="a b",
        literary_form="Fiction",
        subjects=[
            timdex.Subject(
                value=["0 a b c d e f g h j k l m n o p q r s t u v x y z"],
                kind="Personal Name",
            ),
            timdex.Subject(
                value=["0 a b c d e f g h k l m n o p r s t u v x y z"],
                kind="Corporate Name",
            ),
            timdex.Subject(value=["0 a v x y z"], kind="Topical Term"),
            timdex.Subject(value=["0 a v x y z"], kind="Geographic Name"),
        ],
        summary=["a"],
    )


def test_marc_record_with_blank_optional_fields_transforms_correctly():
    marc_xml_records = parse_xml_records(
        "tests/fixtures/marc/marc_record_blank_optional_fields.xml"
    )
    output_records = Marc("alma", marc_xml_records)
    assert next(output_records) == timdex.TimdexRecord(
        source="MIT Alma",
        source_link=(
            "https://mit.primo.exlibrisgroup.com/discovery/fulldisplay?vid="
            "01MIT_INST:MIT&docid=alma990027185640106761"
        ),
        timdex_record_id="alma:990027185640106761",
        title="Title not provided",
        citation=(
            "Title not provided. https://mit.primo.exlibrisgroup.com/discovery/"
            "fulldisplay?vid=01MIT_INST:MIT&docid=alma990027185640106761"
        ),
        content_type=["Not specified"],
    )


def test_marc_record_with_missing_optional_fields_transforms_correctly():
    marc_xml_records = parse_xml_records(
        "tests/fixtures/marc/marc_record_missing_optional_fields.xml"
    )
    output_records = Marc("alma", marc_xml_records)
    assert next(output_records) == timdex.TimdexRecord(
        source="MIT Alma",
        source_link="https://mit.primo.exlibrisgroup.com/discovery/fulldisplay?vid="
        "01MIT_INST:MIT&docid=alma990027185640106761",
        timdex_record_id="alma:990027185640106761",
        title="Title not provided",
        citation=(
            "Title not provided. https://mit.primo.exlibrisgroup.com/discovery/"
            "fulldisplay?vid=01MIT_INST:MIT&docid=alma990027185640106761"
        ),
        content_type=["Not specified"],
    )


def test_create_subfield_value_list_from_datafield_with_values():
    marc_xml_records = parse_xml_records(
        "tests/fixtures/marc/marc_record_all_fields.xml"
    )
    datafield = next(marc_xml_records).find_all("datafield", tag="130")[0]
    assert Marc.create_subfield_value_list_from_datafield(datafield, "ad") == [
        "Main Entry",
        "Date 1",
        "Date 2",
    ]


def test_create_subfield_value_list_from_datafield_with_blank_values():
    marc_xml_records = parse_xml_records(
        "tests/fixtures/marc/marc_record_blank_optional_fields.xml"
    )
    datafield = next(marc_xml_records).find_all("datafield", tag="130")[0]
    assert Marc.create_subfield_value_list_from_datafield(datafield, "ad") == []


def test_create_subfield_value_string_from_datafield_with_values():
    marc_xml_records = parse_xml_records(
        "tests/fixtures/marc/marc_record_all_fields.xml"
    )
    datafield = next(marc_xml_records).find_all("datafield", tag="130")[0]
    assert (
        Marc.create_subfield_value_string_from_datafield(datafield, "ad", " ")
        == "Main Entry Date 1 Date 2"
    )


def test_create_subfield_value_string_from_datafield_with_blank_values():
    marc_xml_records = parse_xml_records(
        "tests/fixtures/marc/marc_record_blank_optional_fields.xml"
    )
    datafield = next(marc_xml_records).find_all("datafield", tag="130")[0]
    assert Marc.create_subfield_value_string_from_datafield(datafield, "ad") == ""


def test_get_main_titles_record_with_title():
    marc_xml_records = parse_xml_records(
        "tests/fixtures/marc/marc_record_all_fields.xml"
    )
    assert Marc.get_main_titles(next(marc_xml_records)) == [
        "Célébration : 10 siècles de musique de noël"
    ]


def test_get_main_titles_record_with_blank_title():
    marc_xml_records = parse_xml_records(
        "tests/fixtures/marc/marc_record_blank_optional_fields.xml"
    )
    assert Marc.get_main_titles(next(marc_xml_records)) == []


def test_get_main_titles_record_without_title():
    marc_xml_records = parse_xml_records(
        "tests/fixtures/marc/marc_record_missing_optional_fields.xml"
    )
    assert Marc.get_main_titles(next(marc_xml_records)) == []


def test_get_source_record_id():
    marc_xml_records = parse_xml_records(
        "tests/fixtures/marc/marc_record_all_fields.xml"
    )
    assert Marc.get_source_record_id(next(marc_xml_records)) == "990027185640106761"
