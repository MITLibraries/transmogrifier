import logging

from bs4 import Tag

import transmogrifier.models as timdex
from transmogrifier.config import load_external_config
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
                "kind": "Preferred Title",
            },
            {
                "tag": "240",
                "subfields": "adfghklmnoprs",
                "kind": "Preferred Title",
            },
            {
                "tag": "246",
                "subfields": "abfghinp",
                "kind": "Varying Form of Title",
            },
            {
                "tag": "730",
                "subfields": "adfghiklmnoprst",
                "kind": "Preferred Title",
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
                marc_content_type_crosswalk.get(leader.string[6:7], leader.string[6:7])
            ]

        # contents
        for datafield in xml.find_all("datafield", tag="505"):
            for contents_value in self.create_subfield_value_list_from_datafield(
                datafield,
                "agrt",
            ):
                for contents_item in contents_value.split(" -- "):
                    fields.setdefault("contents", []).append(
                        contents_item.rstrip(" ./-")
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
        contributor_values = []
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
                    kind_values = []
                    for subfield in datafield.find_all(
                        "subfield", code="e", string=True
                    ):
                        kind_values.append(subfield.string)
                    if kind_values:
                        for kind_value in kind_values:
                            contributor_instance = timdex.Contributor(
                                value=contributor_value.rstrip(" .,"),
                                kind=kind_value.rstrip(" .,"),
                            )
                            if contributor_instance not in contributor_values:
                                contributor_values.append(contributor_instance)
                    else:
                        contributor_instance = timdex.Contributor(
                            value=contributor_value.rstrip(" .,"),
                            kind="Not specified",
                        )
                        if contributor_instance.value not in [
                            existing_contributor.value
                            for existing_contributor in contributor_values
                        ]:
                            contributor_values.append(contributor_instance)
        fields["contributors"] = contributor_values or None

        # dates

        # edition
        edition_values = []
        for datafield in xml.find_all("datafield", tag="250"):
            if edition_value := self.create_subfield_value_string_from_datafield(
                datafield, "ab", " "
            ):
                edition_values.append(edition_value)
        fields["edition"] = " ".join(edition_values) or None

        # file_formats not used in MARC

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

        # rights not used in MARC

        # subjects
        subject_marc_fields = [
            {
                "tag": "600",
                "subfields": "0abcdefghjklmnopqrstuvxyz",
                "kind": "Personal Name",
            },
            {
                "tag": "610",
                "subfields": "0abcdefghklmnoprstuvxyz",
                "kind": "Corporate Name",
            },
            {
                "tag": "650",
                "subfields": "0avxyz",
                "kind": "Topical Term",
            },
            {
                "tag": "651",
                "subfields": "0avxyz",
                "kind": "Geographic Name",
            },
        ]
        for subject_marc_field in subject_marc_fields:
            for datafield in xml.find_all("datafield", tag=subject_marc_field["tag"]):
                if subject_value := (
                    self.create_subfield_value_string_from_datafield(
                        datafield,
                        subject_marc_field["subfields"],
                        " ",
                    )
                ):
                    fields.setdefault("subjects", []).append(
                        timdex.Subject(
                            value=[subject_value.rstrip(" .")],
                            kind=subject_marc_field["kind"],
                        )
                    )

        # summary
        for datafield in xml.find_all("datafield", tag="520"):
            if summary_value := self.create_subfield_value_string_from_datafield(
                datafield, "a", " "
            ):
                fields.setdefault("summary", []).append(summary_value)

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
