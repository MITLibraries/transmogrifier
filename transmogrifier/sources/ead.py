import logging
from typing import Generator, Optional

from bs4 import NavigableString, Tag

import transmogrifier.models as timdex
from transmogrifier.sources.transformer import Transformer

logger = logging.getLogger(__name__)


class Ead(Transformer):
    """EAD transformer."""

    def get_optional_fields(self, xml: Tag) -> Optional[dict]:
        """
        Retrieve optional TIMDEX fields from an EAD XML record.

        Overrides metaclass get_optional_fields() method.

        Args:
            xml: A BeautifulSoup Tag representing a single EAD XML record.
        """
        fields: dict = {}

        try:
            collection_description = xml.metadata.find("archdesc", level="collection")
            collection_description.find_all(True)
        except AttributeError:
            logger.error("Record is missing archdesc element")
            return None

        try:
            collection_description_did = collection_description.did
            collection_description_did.find_all(True)
        except AttributeError:
            logger.error("Record is missing archdesc > did element")
            return None

        # alternate_titles

        # If the record has more than one main title, add extras to alternate_titles
        for index, title in enumerate(self.get_main_titles(xml)):
            if index > 0 and title:
                fields.setdefault("alternate_titles", []).append(
                    timdex.AlternateTitle(value=title)
                )

        # contributors
        for origination_element in collection_description_did.find_all("origination"):
            for name_element in origination_element.find_all(True, recursive=False):
                if name_value := self.create_string_from_mixed_value(name_element):
                    fields.setdefault("contributors", []).append(
                        timdex.Contributor(
                            value=name_value,
                            kind=origination_element.get("label"),
                            identifier=self.generate_name_identifier_url(name_element),
                        )
                    )

        return fields

    @classmethod
    def create_list_from_mixed_value(
        cls, xml_element: Tag, skipped_elements: list = []
    ) -> list:
        """
        Create a list of strings from an XML element value that contains a mix of strings
        and XML elements. This method is used for fields where .stripped_strings
        pulls in unnecessary formatting.

        Args:
            xml_element: An XML element that may contain a value consisting of
            strings and XML elements.
            skipped_elements: Elements that should be skipped when parsing the mixed
            value.
        """

        value_list = []
        for contents_child in xml_element.contents:
            for value in cls.parse_mixed_value(contents_child, skipped_elements):
                value_list.append(value)
        return value_list

    @classmethod
    def create_string_from_mixed_value(
        cls, xml_element: Tag, separator: str = "", skipped_elements: list = []
    ) -> str:
        """
        Create a joined string from a list of strings from an XML element value
        that contains a mix of strings and XML elements. This method is used for
        fields where .stripped_strings pulls in unnecessary formatting.

        Args:
            xml_element: An XML element that may contain a value consisting of
            strings and XML elements.
            separator: An optional separator string to use when joining values.
            skipped_elements: Elements that should be skipped when parsing the mixed
            value.
        """
        return separator.join(
            cls.create_list_from_mixed_value(xml_element, skipped_elements)
        )

    @classmethod
    def generate_name_identifier_url(cls, name_element: Tag) -> Optional[list]:
        """
        Generate a full name identifier URL with the specified scheme.

        Args:
            name_element: A BeautifulSoup Tag representing an EAD
                name XML field.
        """
        if name_element.get("authfilenumber"):
            source = name_element.get("source")
            if source in ["lcnaf", "naf"]:
                base_url = "https://lccn.loc.gov/"
            elif source == "snac":
                base_url = "https://snaccooperative.org/view/"
            elif source == "viaf":
                base_url = "http://viaf.org/viaf/"
            else:
                base_url = ""
            return [base_url + name_element["authfilenumber"]]
        else:
            return None

    @classmethod
    def get_main_titles(cls, xml: Tag) -> list[str]:
        """
        Retrieve main title(s) from an EAD XML record.

        Overrides metaclass get_main_titles() method.

        Args:
            xml: A BeautifulSoup Tag representing a single EAD XML record.
        """
        try:
            unit_titles = xml.metadata.find(
                "archdesc", level="collection"
            ).did.find_all("unittitle")
        except AttributeError:
            return []
        return [
            title.strip()
            for unit_title in unit_titles
            if (title := cls.create_string_from_mixed_value(unit_title, "", ["num"]))
        ]

    @classmethod
    def get_source_record_id(cls, xml: Tag) -> str:
        """
        Get the source record ID from an EAD XML record.

        Overrides metaclass get_source_record_id() method.

        Args:
            xml: A BeautifulSoup Tag representing a single EAD XML record.
        """
        return xml.header.identifier.string.split("//")[1]

    @classmethod
    def parse_mixed_value(cls, item: type, skipped_elements: list) -> Generator:
        """
        Parse an item in a mixed value of XML elements and strings according to its type.
        Recursive given the unpredictable structure of EAD values.

        Args:
            item: An item in a mixed value that may be a BeautifulSoup NavigableString or
            Tag.
            skipped_elements: Elements that should be skipped when parsing the mixed
            value.
        """
        if type(item) == NavigableString and item:
            yield item
        elif type(item) == Tag and item.name not in skipped_elements:
            for contents_item in item.contents:
                for contents_item in cls.parse_mixed_value(
                    contents_item, skipped_elements
                ):
                    yield contents_item
