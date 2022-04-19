from defusedxml import ElementTree as ET

from transmogrifier.datacite import (
    create_instance_list_from_xml,
    create_kwargs_from_datacite_xml,
    create_value_list_from_xml,
    get_instance_value_from_xml,
    populate_instance_attributes_from_xml,
)
from transmogrifier.models import Contributor, Date, Identifier, Note


def test_create_instance_list_from_xml_empty(datacite_record_jpal_minimal):
    xml_element = ET.fromstring(datacite_record_jpal_minimal)
    instance_list = create_instance_list_from_xml(
        xml_element,
        ".//datacite:contributor",
        Contributor,
        {
            "kind": "contributorType",
            "affiliation": "affiliation",
            "identifier": "nameIdentifier",
        },
        "datacite:contributorName",
    )
    assert instance_list == []


def test_create_instance_list_from_xml_full(datacite_record_jpal_full):
    xml_element = ET.fromstring(datacite_record_jpal_full)
    instance_list = create_instance_list_from_xml(
        xml_element,
        ".//datacite:contributor",
        Contributor,
        {
            "kind": "contributorType",
            "affiliation": "affiliation",
            "identifier": "nameIdentifier",
        },
        "datacite:contributorName",
    )
    assert instance_list == [
        Contributor(
            value="Banerji, Rukmini",
            kind="ContactPerson",
        ),
        Contributor(
            value="Berry, James",
            kind="ContactPerson",
        ),
        Contributor(
            value="Shotland, Marc",
            kind="ContactPerson",
        ),
    ]


def test_create_kwargs_from_datacite_xml(datacite_record_jpal_full):
    kwargs = create_kwargs_from_datacite_xml(
        datacite_record_jpal_full, "http://example.example/"
    )
    assert kwargs == {
        "content_type": ["Dataset"],
        "contributors": [
            Contributor(
                value="Banerji, Rukmini",
                kind="ContactPerson",
            ),
            Contributor(
                value="Berry, James",
                kind="ContactPerson",
            ),
            Contributor(
                value="Shotland, Marc",
                kind="ContactPerson",
            ),
            Contributor(
                value="Banerji, Rukmini",
                kind="Creator",
            ),
            Contributor(
                value="Berry, James",
                kind="Creator",
            ),
            Contributor(
                value="Shotland, Marc",
                kind="Creator",
            ),
        ],
        "dates": [
            Date(kind="Submitted", value="2017-02-27"),
            Date(kind="Updated", value="2019-06-24"),
            Date(kind="Publication", value="2017"),
        ],
        "identifiers": [Identifier(value="10.7910/DVN/19PPE7", kind="DOI")],
        "notes": [Note(value="Survey Data", kind="ResourceType")],
        "publication_information": ["Harvard Dataverse"],
        "source_link": "http://example.example/10.7910/DVN/19PPE7",
        "timdex_record_id": "jpal:10.7910-DVN-19PPE7",
        "title": "The Impact of Maternal Literacy and Participation Programs: "
        "Evidence from a Randomized Evaluation in India",
    }


def test_create_value_list_from_xml_empty():
    xml_element = ET.fromstring("<dates></dates>")
    value_list = create_value_list_from_xml(xml_element, ".//date")
    assert value_list == []


def test_create_value_list_from_xml_full():
    xml_string = (
        '<dates><date dateType="Submitted">2017-02-27</date>'
        '<date dateType="Updated">2019-06-24</date></dates>'
    )
    xml_element = ET.fromstring(xml_string)
    value_list = create_value_list_from_xml(xml_element, ".//date")
    assert value_list == ["2017-02-27", "2019-06-24"]


def test_get_instance_value_from_xml_child_element():
    xml_string = (
        '<contributor contributorType="ContactPerson">'
        "<contributorName>Banerji, Rukmini</contributorName></contributor>"
    )
    xml_element = ET.fromstring(xml_string)
    value = get_instance_value_from_xml(xml_element, "contributorName")
    assert value == "Banerji, Rukmini"


def test_get_instance_value_from_xml_no_child_element():
    xml_string = '<date dateType="Submitted">2017-02-27</date>'
    xml_element = ET.fromstring(xml_string)
    value = get_instance_value_from_xml(xml_element)
    assert value == "2017-02-27"


def test_populate_instance_attributes_from_xml_empty():
    date = Date()
    xml_string = "<date>2017-02-27</date>"
    xml_element = ET.fromstring(xml_string)
    date = populate_instance_attributes_from_xml(
        date, xml_element, {"kind": "dateType"}
    )
    assert date.kind is None


def test_populate_instance_attributes_from_xml_full():
    date = Date()
    xml_string = '<date dateType="Submitted">2017-02-27</date>'
    xml_element = ET.fromstring(xml_string)
    date = populate_instance_attributes_from_xml(
        date, xml_element, {"kind": "dateType"}
    )
    assert date.kind == "Submitted"
