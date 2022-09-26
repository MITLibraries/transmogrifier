import logging

from bs4 import Tag

import transmogrifier.models as timdex
from transmogrifier.sources.transformer import Transformer

logger = logging.getLogger(__name__)


class Marc(Transformer):
    """Marc transformer."""

    def get_optional_fields(self, xml: Tag) -> dict:
        """
        Retrieve optional TIMDEX fields from a MARC XML record.

        Overrides metaclass get_optional_fields() method.

        Args:
            xml: A BeautifulSoup Tag representing a single MARC XML record.
        """
        fields: dict = {}

        # alternate_titles
        alternate_title_marc_data = {
            "130": ("adfghklmnoprst", "Main Entry - Uniform Title"),
            "240": ("adfghklmnoprs", "Uniform Title"),
            "246": ("abfghinp", "Varying Form of Title"),
            "730": ("adfghiklmnoprst", "Added Entry - Uniform Title"),
            "740": ("anp", "Added Entry - Uncontrolled Related/Analytical Title"),
        }
        for marc_tag, marc_field_data in alternate_title_marc_data.items():
            for datafield in xml.find_all("datafield", tag=marc_tag):
                if alternate_title_value := (
                    self.create_subfield_value_string_from_datafield(
                        datafield,
                        marc_field_data[0],
                        " ",
                    )
                ):
                    fields.setdefault("alternate_titles", []).append(
                        timdex.AlternateTitle(
                            value=alternate_title_value,
                            kind=marc_field_data[1],
                        )
                    )

        # call_numbers
        call_numbers_marc_data = {
            "050": ("a", ""),
            "082": ("a", ""),
        }
        for marc_tag, marc_field_data in call_numbers_marc_data.items():
            for datafield in xml.find_all("datafield", tag=marc_tag):
                if call_number_value := self.create_subfield_value_string_from_datafield(
                    datafield,
                    marc_field_data[0],
                ):
                    fields.setdefault("call_numbers", []).append(call_number_value)

        # citation

        # content_type

        # contents

        # contributors

        # dates

        # edition

        # file_formats

        # format

        # funding_information

        # holdings

        # identifiers

        # languages

        # links

        # literary_form
        # Literary form is applicable to Book (BK) material configurations and indicated
        # by leader "Type of Record" position = "Language Material" or "Manuscript
        # language material" and "Bibliographic level" position =
        # "Monographic component part," "Collection," "Subunit," or "Monograph/Item."
        if leader := xml.find("leader", string=True):
            if leader.string[6:7] in "at" and leader.string[7:8] in "acdm":
                if fixed_length_data := xml.find(
                    "controlfield", tag="008", string=True
                ):
                    if fixed_length_data.string[33:34] in "0se":
                        fields["literary_form"] = "Nonfiction"
                    elif fixed_length_data.string[33:34]:
                        fields["literary_form"] = "Fiction"

        # locations

        # notes

        # numbering

        # physical_description

        # publication_frequency

        # publication_information

        # related_items

        # rights

        # subjects

        # summary

        return fields

    @staticmethod
    def get_main_titles(xml: Tag) -> list[str]:
        """
        Retrieve main title(s) from a MARC XML record.

        Overrides metaclass get_main_titles() method.

        Args:
            xml: A BeautifulSoup Tag representing a single MARC XML record.
        """
        main_title_values = [
            title
            for datafield in xml.find_all("datafield", tag="245")
            if (
                title := Marc.create_subfield_value_string_from_datafield(
                    datafield, "abfgknps", " "
                )
            )
        ]
        if main_title_values:
            return main_title_values
        else:
            return []

    @staticmethod
    def get_source_record_id(xml: Tag) -> str:
        """
        Get the source record ID from a MARC XML record.

        Overrides metaclass get_source_record_id() method.

        Args:
            xml: A BeautifulSoup Tag representing a single MARC XML record.
        """
        return xml.find("controlfield", tag="001", string=True).string

    @staticmethod
    def create_subfield_value_list_from_datafield(
        xml_element: Tag,
        subfield_codes: str,
    ) -> list:
        """
        Create a list of values from the specified subfields of a
        datafield element.

        Args:
            xml_element: A BeautifulSoup Tag representing a single MARC XML element.
            subfield_codes: The codes of the subfields to extract.
        """
        value_list = []
        for subfield in xml_element.children:
            if (
                type(subfield) == Tag
                and subfield.get("code", "") in subfield_codes
                and subfield.string
            ):
                value_list.append(subfield.string)
        return value_list

    @staticmethod
    def create_subfield_value_string_from_datafield(
        xml_element: Tag,
        subfield_codes: str,
        separator: str = "",
    ) -> str:
        """
        Create a joined string from a list of subfield values from datafield XML element.

        Args:
            xml_element: A BeautifulSoup Tag representing a single MARC XML element.
            subfield_codes: The codes of the subfields to extract.
            separator: An optional separator string to use when joining values.
        """
        return separator.join(
            Marc.create_subfield_value_list_from_datafield(xml_element, subfield_codes)
        )
