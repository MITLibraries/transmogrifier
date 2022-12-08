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
            "Célébration : 10 siècles de musique de noël. 2016. "
            "New York : New Press : Distributed by W.W. Norton, 2005. Language material. "
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
        dates=[timdex.Date(kind="Publication date", value="2016")],
        edition="9th ed. / Nick Ray ... [et al.]. Unabridged.",
        identifiers=[
            timdex.Identifier(value="2005022317", kind="LCCN"),
            timdex.Identifier(value="9781250185969. hardcover", kind="ISBN"),
            timdex.Identifier(
                value="0878426914. paperback. alkaline paper", kind="ISBN"
            ),
            timdex.Identifier(value="0033-0736", kind="ISSN"),
            timdex.Identifier(value="0095-9014", kind="ISSN"),
            timdex.Identifier(
                value="10.1596/978-0-8213-7468-9. doi", kind="Other Identifier"
            ),
            timdex.Identifier(value="1234567890. score. sewn", kind="Other Identifier"),
            timdex.Identifier(value="1312285564", kind="OCLC Number"),
            timdex.Identifier(value="on1312285564", kind="OCLC Number"),
        ],
        languages=[
            "No linguistic content",
            "English",
            "Spanish",
            "French",
            "Finnish",
            "Latin",
            "German",
            "Sung in French or Latin",
            "Sung in French",
        ],
        links=[
            timdex.Link(
                url="http://catalog.hathitrust.org/api/volumes/oclc/1606890.html",
                kind="Hathi Trust",
            ),
            timdex.Link(
                url="http://www.rsc.org/Publishing/Journals/cb/PreviousIssue.asp",
                kind="Digital object URL",
                restrictions="Access available on website of subsequent title: "
                "Highlights in chemical biology",
                text="Display text",
            ),
        ],
        literary_form="Nonfiction",
        locations=[
            timdex.Location(value="France", kind="Place of Publication"),
            timdex.Location(value="Germany", kind="Geographic Name"),
            timdex.Location(value="Austria", kind="Geographic Name"),
            timdex.Location(
                value="Africa - Nile River - Sixth Cataract",
                kind="Hierarchical Place Name",
            ),
            timdex.Location(value="Austria - Vienna", kind="Hierarchical Place Name"),
        ],
        notes=[
            timdex.Note(
                value=["arranged by the Arts Council of Great Britain"],
                kind="Title Statement of Responsibility",
            ),
            timdex.Note(value=["Opera in 5 acts"], kind="General Note"),
            timdex.Note(
                value=[
                    "Libretto based on: A midsummer night's dream by William Shakespeare"
                ],
                kind="General Note",
            ),
            timdex.Note(
                value=["Thesis (D.SC.)--University of London"], kind="Dissertation Note"
            ),
            timdex.Note(
                value=[
                    "M. Eng. Massachusetts Institute of Technology, Department of "
                    "Electrical Engineering and Computer Science 2004"
                ],
                kind="Dissertation Note",
            ),
            timdex.Note(
                value=["Includes bibliographical references and index"],
                kind="Bibliography Note",
            ),
            timdex.Note(value=["Bibliography: p. 186-202"], kind="Bibliography Note"),
            timdex.Note(
                value=["Producer, Toygun Kirali"],
                kind="Creation/Production Credits Note",
            ),
            timdex.Note(
                value=["Producer : Monika Feszler"],
                kind="Creation/Production Credits Note",
            ),
            timdex.Note(
                value=["Lamoureux Concerts Orchestra ; Igor Markevitch, conductor"],
                kind="Participant or Performer Note",
            ),
            timdex.Note(
                value=["Berlin Symphony Orchestra ; Kurt Sanderling, conductor"],
                kind="Participant or Performer Note",
            ),
            timdex.Note(
                value=["Suspended publication 1944-52"],
                kind="Numbering Peculiarities Note",
            ),
            timdex.Note(
                value=["Some numbers combined"], kind="Numbering Peculiarities Note"
            ),
            timdex.Note(value=["Canada"], kind="Geographic Coverage Note"),
            timdex.Note(value=["Mexico"], kind="Geographic Coverage Note"),
            timdex.Note(
                value=[
                    "Electronic reproduction. New York : Springer, 2008. Mode of access: "
                    "World Wide Web. System requirements: Web browser. Title from title "
                    "screen (viewed on June 27, 2008). Access may be restricted to users "
                    "at subscribing institutions"
                ],
                kind="Reproduction Note",
            ),
            timdex.Note(
                value=[
                    "Microfiche. Washington : U.S. Govt. Print. Off., 1981. 1 microfiche "
                    "; 11 x 15 cm"
                ],
                kind="Reproduction Note",
            ),
            timdex.Note(
                value=[
                    "First published in United States New York : Ballantine Books, an "
                    "imprint of Random House, a division of Penguin Random House, 2021"
                ],
                kind="Original Version Note",
            ),
            timdex.Note(
                value=[
                    "Originally published New York : Garland, 1987. Series statement 1 "
                    "Series statement 2"
                ],
                kind="Original Version Note",
            ),
            timdex.Note(
                value=["Hard copy version record"],
                kind="Source of Description Note",
            ),
            timdex.Note(
                value=["Paper copy version record"],
                kind="Source of Description Note",
            ),
            timdex.Note(
                value=["Rare Book copy: Advance copy notice inserted"],
                kind="Local Note",
            ),
            timdex.Note(value=["Advance copy notice inserted"], kind="Local Note"),
        ],
        numbering="-Bd. 148, 4 (dez. 1997). Began in 1902.",
        physical_description=(
            "484 p. : ill. ; 30 cm. + 1 CD-ROM (4 3/4 in.). 1 DVD-ROM "
            "(4 3/4 in.). 1 vocal score (248 p.) ; 31 cm."
        ),
        publication_frequency=["Six no. a year", "Three times a year"],
        publication_information=[
            "New York : New Press : Distributed by W.W. Norton, 2005",
            "New York : Wiley, c1992",
            "France : Alpha, [2022]",
            "℗2022, ©2022",
        ],
        related_items=[
            timdex.RelatedItem(
                description="Java 2 in plain English",
                relationship="Original Language Version",
            ),
            timdex.RelatedItem(
                description="Java 3; 1, 2",
                relationship="Original Language Version",
            ),
            timdex.RelatedItem(
                description="Geological Society of America data repository (DLC)sn "
                "86025915 (OCoLC)13535209",
                relationship="Has Supplement",
            ),
            timdex.RelatedItem(
                description="Biological Society of America data repository (DLC)sn "
                "86025915 (OCoLC)13535209",
                relationship="Has Supplement",
            ),
            timdex.RelatedItem(
                description="Earthquake engineering and structural dynamics",
                relationship="Supplement To",
            ),
            timdex.RelatedItem(
                description="Earthquake engineering and structural dynamics Vol. 13 "
                "(1985), p. 297-315 Vol. 14 (1986), p. 297-315",
                relationship="Supplement To",
            ),
            timdex.RelatedItem(
                description="Entertainment design 1520-5150",
                relationship="Previous Title",
            ),
            timdex.RelatedItem(
                description="Lighting dimensions 0191-541X (DLC) 79649241 "
                "(OCoLC)3662625",
                relationship="Previous Title",
            ),
            timdex.RelatedItem(
                description="Protist (DLC)sn 98050216 (OCoLC)39018023 1434-4610",
                relationship="Subsequent Title",
            ),
            timdex.RelatedItem(
                description="Protestant 1434-4610",
                relationship="Subsequent Title",
            ),
            timdex.RelatedItem(
                description="Part of: De historien des Ouden en Nieuwen Testaments",
                relationship="Not Specified",
            ),
            timdex.RelatedItem(
                description="Part of: A Small Part of: Nieuwen Testaments",
                relationship="Not Specified",
            ),
            timdex.RelatedItem(
                description="Map and chart series (New York State Geological Survey) ; "
                "no. 53. 0097-3793",
                relationship="In Series",
            ),
            timdex.RelatedItem(
                description="Duo",
                relationship="In Series",
            ),
            timdex.RelatedItem(
                description="Predicasts",
                relationship="In Bibliography",
            ),
            timdex.RelatedItem(
                description="Predicasts Jan. 13, 1975- 13",
                relationship="In Bibliography",
            ),
        ],
        subjects=[
            timdex.Subject(
                value=["Renoir, Jean, - 1894-1979 - Bibliography"],
                kind="Personal Name",
            ),
            timdex.Subject(
                value=["Renoir, Jean, - 1894-1979"],
                kind="Personal Name",
            ),
            timdex.Subject(
                value=["United States. - Federal Bureau of Investigation - History"],
                kind="Corporate Name",
            ),
            timdex.Subject(
                value=["United States. - Federal Bureau of Investigation"],
                kind="Corporate Name",
            ),
            timdex.Subject(
                value=["Musique vocale sacrée - France - 500-1400"],
                kind="Topical Term",
            ),
            timdex.Subject(value=["Sacred songs, Unaccompanied"], kind="Topical Term"),
            timdex.Subject(
                value=["Great Plains - Climate"],
                kind="Geographic Name",
            ),
            timdex.Subject(value=["Great Plains"], kind="Geographic Name"),
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
            "a b f g k n p s. 2016. a b c d e f. Manuscript language material. "
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
        dates=[timdex.Date(kind="Publication date", value="2016")],
        edition="a b",
        identifiers=[
            timdex.Identifier(value="q", kind="ISBN"),
            timdex.Identifier(value="q", kind="Other Identifier"),
        ],
        languages=[
            "No linguistic content",
            "a",
            "b",
            "d",
            "e",
            "f",
            "g",
            "h",
            "j",
            "k",
            "m",
            "n",
        ],
        links=[
            timdex.Link(url="u", kind="3", restrictions="z", text="y"),
            timdex.Link(url="u", kind="3", restrictions="z", text="y"),
        ],
        literary_form="Fiction",
        locations=[
            timdex.Location(value="France", kind="Place of Publication"),
            timdex.Location(
                value="a - b - c - d - e - f - g - h",
                kind="Hierarchical Place Name",
            ),
        ],
        notes=[
            timdex.Note(value=["c"], kind="Title Statement of Responsibility"),
            timdex.Note(value=["a"], kind="General Note"),
            timdex.Note(value=["a b c d g"], kind="Dissertation Note"),
            timdex.Note(value=["a"], kind="Bibliography Note"),
            timdex.Note(value=["a"], kind="Creation/Production Credits Note"),
            timdex.Note(value=["a"], kind="Participant or Performer Note"),
            timdex.Note(value=["a"], kind="Numbering Peculiarities Note"),
            timdex.Note(value=["a"], kind="Geographic Coverage Note"),
            timdex.Note(value=["a b c d e f m n"], kind="Reproduction Note"),
            timdex.Note(
                value=["a b c e f k l m n o p t x z"], kind="Original Version Note"
            ),
            timdex.Note(value=["a"], kind="Source of Description Note"),
            timdex.Note(value=["a"], kind="Local Note"),
        ],
        physical_description="a b c e f g",
        publication_information=["a b c d e f", "a b c"],
        related_items=[
            timdex.RelatedItem(
                description="a b c d g h i k m n o r s t u w x y z",
                relationship="Original Language Version",
            ),
            timdex.RelatedItem(
                description="a b c d g h i k m n o r s t u w x y z",
                relationship="Has Supplement",
            ),
            timdex.RelatedItem(
                description="a b c d g h i k m n o r s t u w x y z",
                relationship="Supplement To",
            ),
            timdex.RelatedItem(
                description="a b c d g h i k m n o r s t u w x y z",
                relationship="Previous Title",
            ),
            timdex.RelatedItem(
                description="a b c d g h i k m n o r s t u w x y z",
                relationship="Subsequent Title",
            ),
            timdex.RelatedItem(
                description="a b c d g h i k m n o r s t u w x y z",
                relationship="Not Specified",
            ),
            timdex.RelatedItem(
                description="a d f g h k l m n o p r s t v w x",
                relationship="In Series",
            ),
            timdex.RelatedItem(
                description="a b c x",
                relationship="In Bibliography",
            ),
        ],
        subjects=[
            timdex.Subject(
                value=[
                    "a - b - c - d - e - f - g - h - j - k - l - m - n - o - p - q - r - "
                    "s - t - u - v - x - y - z"
                ],
                kind="Personal Name",
            ),
            timdex.Subject(
                value=[
                    "a - b - c - d - e - f - g - h - k - l - m - n - o - p - r - s - t - "
                    "u - v - x - y - z"
                ],
                kind="Corporate Name",
            ),
            timdex.Subject(value=["a - v - x - y - z"], kind="Topical Term"),
            timdex.Subject(value=["a - v - x - y - z"], kind="Geographic Name"),
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
