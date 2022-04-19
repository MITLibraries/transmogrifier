from typing import Any, Dict, Optional

from defusedxml import ElementTree as ET  # type:ignore

from transmogrifier.config import NAMESPACES
from transmogrifier.models import Contributor, Date, Identifier, Note


def create_kwargs_from_datacite_xml(
    datacite_xml_string: str, source_link_url: str
) -> Dict[str, Any]:
    """
    Create a kwargs dict from Datacite XML to be used by a data source transform function
    to create a TimdexRecord instance.
    Args:
        datacite_xml_string: A Datacite XML string to parse for values.
        source_link_url: A URL to prepend the DOI for a direct link to the dataset's
        metadata record.
    """
    xml_element = ET.fromstring(datacite_xml_string)
    kwargs = {}
    titles_xml = xml_element.findall(".//datacite:title", NAMESPACES)
    for title_xml in [t for t in titles_xml if "titleType" not in t.attrib]:
        kwargs["title"] = title_xml.text

    identifiers_xml = xml_element.findall(".//datacite:identifier", NAMESPACES)
    for identifier_xml in [
        i
        for i in identifiers_xml
        if "identifierType" in i.attrib and i.attrib["identifierType"] == "DOI"
    ]:
        doi = identifier_xml.text
        kwargs["timdex_record_id"] = f"jpal:{doi.replace('/', '-')}"
        kwargs["identifiers"] = [Identifier(value=doi, kind="DOI")]
        kwargs["source_link"] = source_link_url + doi

    contributors = create_instance_list_from_xml(
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
    creators = create_instance_list_from_xml(
        xml_element,
        ".//datacite:creator",
        Contributor,
        {
            "affiliation": "affiliation",
            "identifier": "nameIdentifier",
        },
        "datacite:creatorName",
    )
    for creator in creators:
        creator.kind = "Creator"
    kwargs["contributors"] = contributors + creators

    kwargs["publication_information"] = create_value_list_from_xml(
        xml_element, ".//datacite:publisher"
    )

    dates = create_instance_list_from_xml(
        xml_element,
        ".//datacite:date",
        Date,
        {
            "kind": "dateType",
            "note": "dateInformation",
        },
    )
    publication_years = []
    publication_years_xml = xml_element.findall(
        ".//datacite:publicationYear", NAMESPACES
    )
    for publication_year_xml in publication_years_xml:
        publication_year = Date(value=publication_year_xml.text, kind="Publication")
        publication_years.append(publication_year)
    kwargs["dates"] = dates + publication_years

    resource_types = []
    content_types = []
    resource_types_xml = xml_element.findall(".//datacite:resourceType", NAMESPACES)
    for resource_type_xml in resource_types_xml:
        if resource_type_xml.text is not None:
            resource_types.append(
                Note(value=resource_type_xml.text, kind="ResourceType")
            )
        if "resourceTypeGeneral" in resource_type_xml.attrib:
            content_types.append(resource_type_xml.attrib["resourceTypeGeneral"])
    kwargs["notes"] = resource_types
    kwargs["content_type"] = content_types

    kwargs = {k: v for k, v in kwargs.items() if v}
    return kwargs


def create_instance_list_from_xml(
    xml_element: Any,
    xpath: str,
    instance_class: Any,
    attribute_mapping_dict: Dict[str, str],
    value_child_element: Optional[str] = None,
) -> list[Any]:
    """
    Create a list of instances of the specificed class and populate those instances
    with data from the XML element being parsed.
    Args:
        xml_element: The XML element to parse.
        xpath: The xpath to use for parsing the XML element for values.
        instance_class: The class used to create the instances that will be populated.
        attribute_mapping_dict: A dict mapping instance attributes to their source XML
        attributes. Passed to the populate_instance_attributes_from_xml function.
        value_child_element_tag: The tag of the child element that contains the value for
        the instance's value attribute. Passed to the get_instance_value_from_xml
        function.
    """
    instance_list = []
    xml_elements = xml_element.findall(xpath, NAMESPACES)
    for xml_element in xml_elements:
        instance = instance_class(
            value=get_instance_value_from_xml(xml_element, value_child_element)
        )
        instance = populate_instance_attributes_from_xml(
            instance,
            xml_element,
            attribute_mapping_dict,
        )
        instance_list.append(instance)
    return instance_list


def create_value_list_from_xml(
    xml_element: Any,
    xpath: str,
) -> list[Any]:
    """
    Args:
        xml_element: The XML element to parse.
        xpath: The xpath to use for parsing the XML element for values.
    """
    value_list = []
    xml_elements = xml_element.findall(xpath, NAMESPACES)
    for xml_element in xml_elements:
        value_list.append(xml_element.text)
    return value_list


def get_instance_value_from_xml(
    xml_element: Any, child_element_tag: Optional[str] = None
) -> str:
    """
    Get the value for populating an instance's value attribute by parsing an XML element.
    If no child element is specified, the text attribute of the XML element will be
    retrieved.
    Args:
        xml_element: The XML element to parse.
        child_element_tag: The tag of the child element that contains the value for
        the instance's value attribute.
    """
    if child_element_tag:
        value = xml_element.find(child_element_tag, NAMESPACES).text
    else:
        value = xml_element.text
    return value


def populate_instance_attributes_from_xml(
    class_instance: Any,
    xml_element: Any,
    attribute_mapping_dict: dict,
) -> Any:
    """
    Populate the attributes of a instance from an XML element based on a mapping dict.
    Args:
        class_instance: The instance of a class to populate.
        xml_element: The XML element containing the necessary attribute values.
        attribute_mapping_dict: A dict mapping instance attributes to their source XML
        attributes.
    """
    for class_attribute, xml_attribute in attribute_mapping_dict.items():
        if xml_attribute in xml_element.attrib:
            setattr(class_instance, class_attribute, xml_element.attrib[xml_attribute])
    return class_instance
