import logging

from bs4 import Tag

import transmogrifier.models as timdex
from transmogrifier.config import load_external_config
from transmogrifier.helpers import crosswalk_value
from transmogrifier.sources.transformer import Transformer

logger = logging.getLogger(__name__)


marc_content_type_crosswalk = load_external_config(
    "config/marc_content_type_crosswalk.json"
)


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

        leader = xml.find("leader", string=True)

        # alternate_titles
        alternate_title_marc_fields = [
            {
                "tag": "130",
                "subfields": "adfghklmnoprst",
                "kind": "Uniform Title",
            },
            {
                "tag": "240",
                "subfields": "adfghklmnoprs",
                "kind": "Uniform Title",
            },
            {
                "tag": "246",
                "subfields": "abfghinp",
                "kind": "Varying Form of Title",
            },
            {
                "tag": "730",
                "subfields": "adfghiklmnoprst",
                "kind": "Uniform Title",
            },
            {
                "tag": "740",
                "subfields": "anp",
                "kind": "Uncontrolled Related/Analytical Title",
            },
        ]
        for alternate_title_marc_field in alternate_title_marc_fields:
            for datafield in xml.find_all(
                "datafield", tag=alternate_title_marc_field["tag"]
            ):
                if alternate_title_value := (
                    self.create_subfield_value_string_from_datafield(
                        datafield,
                        alternate_title_marc_field["subfields"],
                        " ",
                    )
                ):
                    fields.setdefault("alternate_titles", []).append(
                        timdex.AlternateTitle(
                            value=alternate_title_value.rstrip(" .,/"),
                            kind=alternate_title_marc_field["kind"],
                        )
                    )

        # call_numbers
        call_number_marc_fields = [
            {
                "tag": "050",
                "subfields": "a",
            },
            {
                "tag": "082",
                "subfields": "a",
            },
        ]
        for call_number_marc_field in call_number_marc_fields:
            for datafield in xml.find_all(
                "datafield", tag=call_number_marc_field["tag"]
            ):
                for call_number_value in self.create_subfield_value_list_from_datafield(
                    datafield,
                    call_number_marc_field["subfields"],
                ):
                    fields.setdefault("call_numbers", []).append(call_number_value)

        # citation not used in MARC

        # content_type
        if leader:
            fields["content_type"] = [
                crosswalk_value(marc_content_type_crosswalk, leader.string[6:7])
            ]

        # contents
        for datafield in xml.find_all("datafield", tag="505"):
            for contents_value in self.create_subfield_value_list_from_datafield(
                datafield,
                "agrt",
            ):
                if " -- " in contents_value:
                    for contents_item in contents_value.split(" -- "):
                        fields.setdefault("contents", []).append(
                            contents_item.rstrip(" ./-")
                        )
                else:
                    fields.setdefault("contents", []).append(
                        contents_value.rstrip(" ./-")
                    )

        # contributors
        contributor_marc_fields = [
            {
                "tag": "100",
                "subfields": "abcq",
            },
            {
                "tag": "110",
                "subfields": "abc",
            },
            {
                "tag": "111",
                "subfields": "acdfgjq",
            },
            {
                "tag": "700",
                "subfields": "abcq",
            },
            {
                "tag": "710",
                "subfields": "abc",
            },
            {
                "tag": "711",
                "subfields": "acdfgjq",
            },
        ]
        for contributor_marc_field in contributor_marc_fields:
            for datafield in xml.find_all(
                "datafield", tag=contributor_marc_field["tag"]
            ):
                if contributor_value := (
                    self.create_subfield_value_string_from_datafield(
                        datafield,
                        contributor_marc_field["subfields"],
                        " ",
                    )
                ):
                    kind_value = []
                    for subfield in datafield.find_all(
                        "subfield", code="e", string=True
                    ):
                        kind_value.append(subfield.string)
                    fields.setdefault("contributors", []).append(
                        timdex.Contributor(
                            value=contributor_value.rstrip(" .,"),
                            kind=" ".join(kind_value).rstrip(" .")
                            if kind_value
                            else "contributor",
                        )
                    )

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
        if leader:
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
        for subfield in xml_element.find_all(True, string=True):
            if subfield.get("code", "") in subfield_codes:
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

    @staticmethod
    def get_main_titles(xml: Tag) -> list[str]:
        """
        Retrieve main title(s) from a MARC XML record.

        Overrides metaclass get_main_titles() method.

        Args:
            xml: A BeautifulSoup Tag representing a single MARC XML record.
        """
        try:
            main_title_values = []
            if main_title_value := Marc.create_subfield_value_string_from_datafield(
                xml.find("datafield", tag="245"), "abfgknps", " "
            ):
                main_title_values.append(main_title_value.rstrip(" .,/"))
            return main_title_values
        except AttributeError:
            logger.error(
                "Record ID %s is missing a 245 field", Marc.get_source_record_id(xml)
            )
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
