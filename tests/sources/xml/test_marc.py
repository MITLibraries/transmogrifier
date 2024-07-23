# ruff: noqa: E501, SLF001
import logging

import pytest
from bs4 import BeautifulSoup  # type: ignore[import-untyped]

import transmogrifier.models as timdex
from transmogrifier.exceptions import SkippedRecordEvent
from transmogrifier.sources.xml.marc import Marc


def create_marc_source_record_stub(
    leader_field_insert: str = "<leader>03282nam  2200721Ki 4500</leader>",
    control_field_insert: str = (
        '<controlfield tag="008">170906s2016    fr mun| o         e zxx d</controlfield>'
    ),
    datafield_insert: str = "",
):
    """
    Create source record for unit tests.

    Args:
        leader_field_insert (str): A string representing a MARC fixed length 'leader'
            XML element. Defaults to a dummy value.
        control_field_insert (str): A string representing a MARC fixed length
            'general info control field' (i.e., code 008) XML element.
            Defaults to a dummy value.
        datafield_insert (str): A string representing a MARC 'datafield' XML element.

    Note: A source record for "missing" field method tests can be created by
        setting datafield_insert = "" (the default).
    """
    xml_string = """
        <collection>
            <record>
                {leader_field_insert}
                {control_field_insert}
                <controlfield tag="001">990027185640106761</controlfield>
                {datafield_insert}
            </record>
        </collection>
    """

    return BeautifulSoup(
        xml_string.format(
            leader_field_insert=leader_field_insert,
            control_field_insert=control_field_insert,
            datafield_insert=datafield_insert,
        ),
        "xml",
    )


def test_marc_record_all_fields_transform_correctly():
    marc_xml_records = Marc.parse_source_file(
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
            timdex.AlternateTitle(value="Uniform Date 1 Date 2", kind="Preferred Title"),
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
            "New York : New Press. Language material. "
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
        dates=[
            timdex.Date(kind="Publication date", value="2016"),
            timdex.Date(kind="Publication date", value="2005"),
        ],
        edition="9th ed. / Nick Ray ... [et al.]. Unabridged.",
        holdings=[
            timdex.Holding(
                call_number="PL2687.L8.A28 1994",
                collection="Stacks",
                format="Print volume",
                location="Hayden Library",
            ),
            timdex.Holding(
                call_number="QD79.C4.C485 1983",
                collection="Off Campus Collection",
                format="Print volume",
                location="Library Storage Annex",
                note="pt.A",
            ),
            timdex.Holding(
                collection="HeinOnline U.S. Congressional Documents Library",
                format="electronic resource",
                location=(
                    "http://BLCMIT.NaxosMusicLibrary.com/catalogue/item.asp?cid=ACC24383"
                ),
                note="Available from 06/01/2001 volume: 1 issue: 1.",
            ),
            timdex.Holding(
                collection="Music Online: Classical Music Library - United States",
                format="electronic resource",
                location="http://BLCMIT.NaxosMusicLibrary.com/catalogue/item.asp?"
                "cid=19029653",
            ),
            timdex.Holding(
                collection="O'Reilly Online Learning",
                format="electronic resource",
                location="http://link-resolver-url",
            ),
        ],
        identifiers=[
            timdex.Identifier(value="2005022317", kind="LCCN"),
            timdex.Identifier(value="9781250185969. hardcover", kind="ISBN"),
            timdex.Identifier(value="0878426914. paperback. alkaline paper", kind="ISBN"),
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
                kind="Digital object URL",
                text="HeinOnline U.S. Congressional Documents Library",
                url="http://BLCMIT.NaxosMusicLibrary.com/catalogue/item.asp?"
                "cid=ACC24383",
            ),
            timdex.Link(
                kind="Digital object URL",
                text="Music Online: Classical Music Library - United States",
                url="http://BLCMIT.NaxosMusicLibrary.com/catalogue/item.asp?"
                "cid=19029653",
            ),
            timdex.Link(
                kind="Digital object URL",
                text="O'Reilly Online Learning",
                url="http://link-resolver-url",
            ),
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
            timdex.Location(value="New York", kind="Place of Publication"),
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
        publishers=[
            timdex.Publisher(name="New Press", date="2005", location="New York"),
            timdex.Publisher(name="Wiley", date="c1992", location="New York"),
            timdex.Publisher(name="Alpha", date="[2022]", location="France"),
            timdex.Publisher(date="℗2022,"),
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
    marc_xml_records = Marc.parse_source_file(
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
            timdex.AlternateTitle(value="a b f g h i n p", kind="Varying Form of Title"),
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
            "a b f g k n p s. 2016. a : b. Manuscript language material. "
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
        dates=[
            timdex.Date(kind="Publication date", value="2016"),
        ],
        edition="a b",
        holdings=[
            timdex.Holding(
                call_number="bb",
                collection="Browsery",
                format="VHS",
                location="Hayden Library",
                note="g",
            ),
            timdex.Holding(
                format="electronic resource",
                location="only subfield d",
            ),
            timdex.Holding(
                format="electronic resource",
                location="only subfield f",
            ),
            timdex.Holding(
                format="electronic resource",
                note="only subfield i",
            ),
            timdex.Holding(
                format="electronic resource",
                collection="only subfield j",
            ),
            timdex.Holding(
                format="electronic resource",
                location="only subfield l",
            ),
            timdex.Holding(
                format="electronic resource",
                location="f: d and l present",
            ),
            timdex.Holding(
                format="electronic resource",
                location="l: d present",
            ),
        ],
        identifiers=[
            timdex.Identifier(value="q", kind="ISBN"),
            timdex.Identifier(value="q", kind="Other Identifier"),
        ],
        languages=[
            "No linguistic content",
            "English",
            "French",
            "Spanish",
            "German",
            "Russian",
            "Chinese",
            "Artificial (Other)",
            "Abkhaz",
            "Achinese",
            "Aljamía",
        ],
        links=[
            timdex.Link(
                kind="Digital object URL",
                url="only subfield d",
            ),
            timdex.Link(
                kind="Digital object URL",
                url="only subfield f",
            ),
            timdex.Link(
                kind="Digital object URL",
                url="only subfield l",
            ),
            timdex.Link(
                kind="Digital object URL",
                url="f: d and l present",
            ),
            timdex.Link(
                kind="Digital object URL",
                url="l: d present",
            ),
            timdex.Link(url="u", kind="3", restrictions="z", text="y"),
            timdex.Link(url="u", kind="3", restrictions="z", text="y"),
        ],
        literary_form="Fiction",
        locations=[
            timdex.Location(value="Vietnam, North", kind="Place of Publication"),
            timdex.Location(
                value="a - b - c - d - e - f - g - h",
                kind="Hierarchical Place Name",
            ),
            timdex.Location(value="a", kind="Place of Publication"),
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
        publishers=[
            timdex.Publisher(name="b", date="c", location="a"),
            timdex.Publisher(name="b", date="c", location="a"),
        ],
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
    marc_xml_records = Marc.parse_source_file(
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
    marc_xml_records = Marc.parse_source_file(
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


def test_get_leader_field_success():
    source_record = create_marc_source_record_stub()
    assert Marc._get_leader_field(source_record) == "03282nam  2200721Ki 4500"


def test_get_leader_field_raises_skipped_record_event_if_field_blank():
    source_record = create_marc_source_record_stub(
        leader_field_insert="<leader></leader>"
    )
    with pytest.raises(
        SkippedRecordEvent,
        match=("Record skipped because key information is missing: <leader>."),
    ):
        Marc._get_leader_field(source_record)


def test_get_leader_field_raises_skipped_record_event_if_field_missing():
    source_record = create_marc_source_record_stub(leader_field_insert="")
    with pytest.raises(
        SkippedRecordEvent,
        match=("Record skipped because key information is missing: <leader>."),
    ):
        Marc._get_leader_field(source_record)


def test_get_control_field_success():
    source_record = create_marc_source_record_stub()
    assert Marc._get_control_field(source_record) == (
        "170906s2016    fr mun| o         e zxx d"
    )


def test_get_control_field_raises_skipped_record_event_if_field_blank():
    source_record = create_marc_source_record_stub(
        control_field_insert='<controlfield tag="008"></controlfield>'
    )
    with pytest.raises(
        SkippedRecordEvent,
        match=(
            'Record skipped because key information is missing: <controlfield tag="008">.'
        ),
    ):
        Marc._get_control_field(source_record)


def test_get_control_field_raises_skipped_record_event_if_field_missing():
    source_record = create_marc_source_record_stub(control_field_insert="")
    with pytest.raises(
        SkippedRecordEvent,
        match=(
            'Record skipped because key information is missing: <controlfield tag="008">.'
        ),
    ):
        Marc._get_control_field(source_record)


def test_get_alternate_titles_success():
    source_record = create_marc_source_record_stub(
        datafield_insert=(
            """
            <datafield tag="130" ind1="0" ind2="0">
                <subfield code="a">Main Entry</subfield>
                <subfield code="d">Date 1</subfield>
                <subfield code="d">Date 2</subfield>
            </datafield>
            <datafield tag="240" ind1="0" ind2="0">
                <subfield code="a">Uniform</subfield>
                <subfield code="d">Date 1</subfield>
                <subfield code="d">Date 2</subfield>
            </datafield>
            <datafield tag="246" ind1="0" ind2="0">
                <subfield code="a">Varying Form</subfield>
                <subfield code="b">Of Title 1.</subfield>
            </datafield>
            <datafield tag="730" ind1="0" ind2="0">
                <subfield code="a">Added Entry 2</subfield>
                <subfield code="n">Part 1</subfield>
                <subfield code="n">Part 2</subfield>
            </datafield>
            <datafield tag="740" ind1="0" ind2="0">
                <subfield code="a">Added Entry 1</subfield>
                <subfield code="n">Part 1</subfield>
                <subfield code="n">Part 2</subfield>
            </datafield>
            """
        )
    )
    assert Marc.get_alternate_titles(source_record) == [
        timdex.AlternateTitle(value="Main Entry Date 1 Date 2", kind="Preferred Title"),
        timdex.AlternateTitle(value="Uniform Date 1 Date 2", kind="Preferred Title"),
        timdex.AlternateTitle(
            value="Varying Form Of Title 1", kind="Varying Form of Title"
        ),
        timdex.AlternateTitle(
            value="Added Entry 2 Part 1 Part 2", kind="Preferred Title"
        ),
        timdex.AlternateTitle(
            value="Added Entry 1 Part 1 Part 2",
            kind="Uncontrolled Related/Analytical Title",
        ),
    ]


def test_get_alternate_titles_transforms_correctly_if_fields_blank():
    source_record = create_marc_source_record_stub(
        datafield_insert=(
            """
            <datafield tag="130" ind1="0" ind2="0">
                <subfield code="a"></subfield>
                <subfield code="d"></subfield>
                <subfield code="d"></subfield>
            </datafield>
            """
        )
    )
    assert Marc.get_alternate_titles(source_record) is None


def test_get_alternate_titles_transforms_correctly_if_fields_missing():
    source_record = create_marc_source_record_stub()
    assert Marc.get_alternate_titles(source_record) is None


def test_get_call_numbers_success():
    source_record = create_marc_source_record_stub(
        datafield_insert=(
            """
            <datafield tag="050" ind1=" " ind2="0">
                <subfield code="a">MA123.4</subfield>
                <subfield code="a">LC Call Number 2</subfield>
            </datafield>
            <datafield tag="082" ind1="0" ind2=" ">
                <subfield code="a">123.45</subfield>
                <subfield code="a">Dewey Call Number 2</subfield>
            </datafield>
            <datafield tag="082" ind1="0" ind2=" ">
                <subfield code="a">Dewey Call Number 3</subfield>
            </datafield>
            """
        )
    )
    assert Marc.get_call_numbers(source_record) == [
        "MA123.4",
        "LC Call Number 2",
        "123.45",
        "Dewey Call Number 2",
        "Dewey Call Number 3",
    ]


def test_get_call_numbers_transforms_correctly_if_fields_blank():
    source_record = create_marc_source_record_stub(
        datafield_insert=(
            """
            <datafield tag="050" ind1=" " ind2="0">
                <subfield code="a"></subfield>
            </datafield>
            """
        )
    )
    assert Marc.get_call_numbers(source_record) is None


def test_get_call_numbers_transforms_correctly_if_fields_missing():
    source_record = create_marc_source_record_stub()
    assert Marc.get_call_numbers(source_record) is None


def test_marc_record_missing_leader_skips_record(caplog):
    marc_xml_records = Marc.parse_source_file(
        "tests/fixtures/marc/marc_record_missing_leader.xml"
    )
    output_records = Marc("alma", marc_xml_records)
    assert len(list(output_records)) == 0
    assert output_records.processed_record_count == 1
    assert output_records.skipped_record_count == 1


def test_marc_record_missing_008_skips_record(caplog):
    marc_xml_records = Marc.parse_source_file(
        "tests/fixtures/marc/marc_record_missing_008.xml"
    )
    output_records = Marc("alma", marc_xml_records)
    assert len(list(output_records)) == 0
    assert output_records.processed_record_count == 1
    assert output_records.skipped_record_count == 1


def test_create_subfield_value_list_from_datafield_with_values():
    marc_xml_records = Marc.parse_source_file(
        "tests/fixtures/marc/marc_record_all_fields.xml"
    )
    datafield = next(marc_xml_records).find_all("datafield", tag="130")[0]
    assert Marc.create_subfield_value_list_from_datafield(datafield, "ad") == [
        "Main Entry",
        "Date 1",
        "Date 2",
    ]


def test_create_subfield_value_list_from_datafield_with_blank_values():
    marc_xml_records = Marc.parse_source_file(
        "tests/fixtures/marc/marc_record_blank_optional_fields.xml"
    )
    datafield = next(marc_xml_records).find_all("datafield", tag="130")[0]
    assert Marc.create_subfield_value_list_from_datafield(datafield, "ad") == []


def test_create_subfield_value_string_from_datafield_with_values():
    marc_xml_records = Marc.parse_source_file(
        "tests/fixtures/marc/marc_record_all_fields.xml"
    )
    datafield = next(marc_xml_records).find_all("datafield", tag="130")[0]
    assert (
        Marc.create_subfield_value_string_from_datafield(datafield, "ad", " ")
        == "Main Entry Date 1 Date 2"
    )


def test_create_subfield_value_string_from_datafield_with_blank_values():
    marc_xml_records = Marc.parse_source_file(
        "tests/fixtures/marc/marc_record_blank_optional_fields.xml"
    )
    datafield = next(marc_xml_records).find_all("datafield", tag="130")[0]
    assert Marc.create_subfield_value_string_from_datafield(datafield, "ad") == ""


def test_get_single_subfield_string_returns_expected_string():
    datafield = BeautifulSoup(
        '<datafield><subfield code="found"> the string  </subfield>/<datafield>', "xml"
    )
    assert Marc.get_single_subfield_string(datafield, "found") == "the string"


def test_get_single_subfield_string_returns_none_if_no_string():
    datafield = BeautifulSoup(
        '<datafield><subfield code="empty"></subfield>/<datafield>', "xml"
    )
    assert Marc.get_single_subfield_string(datafield, "empty") is None


def test_get_single_subfield_string_returns_none_if_whitespace_string():
    datafield = BeautifulSoup(
        '<datafield><subfield code="whitespace">    </subfield>/<datafield>', "xml"
    )
    assert Marc.get_single_subfield_string(datafield, "found") is None


def test_json_crosswalk_code_to_name_returns_none_if_invalid(
    caplog, marc_content_type_crosswalk
):
    caplog.set_level(logging.DEBUG)
    assert (
        Marc.json_crosswalk_code_to_name(
            "wrong",
            marc_content_type_crosswalk,
            "record-01",
            "MARC field",
        )
        is None
    )
    assert "Record #record-01 uses an invalid code in MARC field: wrong" in caplog.text


def test_json_crosswalk_code_to_name_returns_name(caplog, marc_content_type_crosswalk):
    assert (
        Marc.json_crosswalk_code_to_name(
            "a",
            marc_content_type_crosswalk,
            "record-01",
            "MARC field",
        )
        == "Language material"
    )


def test_loc_crosswalk_code_to_name_returns_none_if_invalid(
    caplog, loc_country_crosswalk
):
    caplog.set_level(logging.DEBUG)
    assert (
        Marc.loc_crosswalk_code_to_name(
            "wrong", loc_country_crosswalk, "record-01", "country"
        )
        is None
    )
    assert "Record #record-01 uses an invalid country code: wrong" in caplog.text


def test_loc_crosswalk_code_to_name_returns_name_and_logs_warning_if_obsolete(
    caplog, loc_country_crosswalk
):
    caplog.set_level(logging.DEBUG)
    assert (
        Marc.loc_crosswalk_code_to_name(
            "bwr", loc_country_crosswalk, "record-01", "country"
        )
        == "Byelorussian S.S.R"
    )
    assert "Record #record-01 uses an obsolete country code: bwr" in caplog.text


def test_loc_crosswalk_code_to_name_returns_name(caplog, loc_country_crosswalk):
    assert (
        Marc.loc_crosswalk_code_to_name(
            "xxu", loc_country_crosswalk, "record-01", "country"
        )
        == "United States"
    )


def test_get_main_titles_record_with_title():
    marc_xml_records = Marc.parse_source_file(
        "tests/fixtures/marc/marc_record_all_fields.xml"
    )
    assert Marc.get_main_titles(next(marc_xml_records)) == [
        "Célébration : 10 siècles de musique de noël"
    ]


def test_get_main_titles_record_with_blank_title():
    marc_xml_records = Marc.parse_source_file(
        "tests/fixtures/marc/marc_record_blank_optional_fields.xml"
    )
    assert Marc.get_main_titles(next(marc_xml_records)) == []


def test_get_main_titles_record_without_title():
    marc_xml_records = Marc.parse_source_file(
        "tests/fixtures/marc/marc_record_missing_optional_fields.xml"
    )
    assert Marc.get_main_titles(next(marc_xml_records)) == []


def test_get_source_record_id():
    marc_xml_records = Marc.parse_source_file(
        "tests/fixtures/marc/marc_record_all_fields.xml"
    )
    assert Marc.get_source_record_id(next(marc_xml_records)) == "990027185640106761"


def test_record_is_deleted_returns_true_if_deleted():
    deleted_record = Marc.parse_source_file("tests/fixtures/marc/marc_record_deleted.xml")
    assert Marc.record_is_deleted(next(deleted_record)) is True


def test_record_is_deleted_returns_false_if_not_deleted():
    marc_record = Marc.parse_source_file("tests/fixtures/marc/marc_record_all_fields.xml")
    assert Marc.record_is_deleted(next(marc_record)) is False
