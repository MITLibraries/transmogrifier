import logging
from typing import Optional, Union

from bs4 import Tag

import transmogrifier.models as timdex
from transmogrifier.config import load_external_config
from transmogrifier.sources.transformer import Transformer

logger = logging.getLogger(__name__)


country_code_crosswalk = load_external_config("config/loc-countries.xml", "xml")

holdings_collection_crosswalk = load_external_config(
    "config/holdings_collection_crosswalk.json", "json"
)
holdings_format_crosswalk = load_external_config(
    "config/holdings_format_crosswalk.json", "json"
)
holdings_location_crosswalk = load_external_config(
    "config/holdings_location_crosswalk.json", "json"
)

language_code_crosswalk = load_external_config("config/loc-languages.xml", "xml")

marc_content_type_crosswalk = load_external_config(
    "config/marc_content_type_crosswalk.json", "json"
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

        fixed_length_data = xml.find("controlfield", tag="008", string=True)

        leader = xml.find("leader", string=True)

        record_id = Marc.get_source_record_id(xml)

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
                    kind_values = self.create_subfield_value_list_from_datafield(
                        datafield, "e"
                    )
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
        if fixed_length_data:
            fields["dates"] = [
                timdex.Date(
                    kind="Publication date", value=fixed_length_data.string[7:11]
                )
            ]

        # edition
        edition_values = []
        for datafield in xml.find_all("datafield", tag="250"):
            if edition_value := self.create_subfield_value_string_from_datafield(
                datafield, "ab", " "
            ):
                edition_values.append(edition_value)
        fields["edition"] = " ".join(edition_values) or None

        # file_formats

        # format

        # funding_information

        # holdings
        for datafield in xml.find_all("datafield", tag="985"):
            holding_call_number_value = (
                self.create_subfield_value_string_from_datafield(datafield, ["bb"])
            )
            holding_collection_value = ", ".join(
                [
                    holdings_collection_crosswalk.get(
                        holding_collection_value, holding_collection_value
                    )
                    for holding_collection_value in (
                        self.create_subfield_value_list_from_datafield(datafield, "i")
                    )
                ]
            )
            holding_format_value = ", ".join(
                [
                    holdings_format_crosswalk.get(
                        holding_format_value, holding_format_value
                    )
                    for holding_format_value in (
                        self.create_subfield_value_list_from_datafield(datafield, "t")
                    )
                ]
            )
            holding_location_value = ", ".join(
                [
                    holdings_location_crosswalk.get(
                        holding_location_value, holding_location_value
                    )
                    for holding_location_value in (
                        self.create_subfield_value_list_from_datafield(
                            datafield, ["aa"]
                        )
                    )
                ]
            )
            holding_note_value = self.create_subfield_value_string_from_datafield(
                datafield, "g", ", "
            )
            if (
                holding_call_number_value
                or holding_collection_value
                or holding_format_value
                or holding_location_value
                or holding_note_value
            ):
                fields.setdefault("holdings", []).append(
                    timdex.Holding(
                        call_number=holding_call_number_value or None,
                        collection=holding_collection_value or None,
                        format=holding_format_value or None,
                        location=holding_location_value or None,
                        note=holding_note_value or None,
                    )
                )
        for datafield in xml.find_all("datafield", tag="986"):
            holding_collection_value = self.create_subfield_value_string_from_datafield(
                datafield, "j", ", "
            )
            holding_location_value = self.create_subfield_value_string_from_datafield(
                datafield, "f", ", "
            )
            holding_note_value = self.create_subfield_value_string_from_datafield(
                datafield, "ik", ", "
            )
            if holding_collection_value or holding_location_value or holding_note_value:
                fields.setdefault("holdings", []).append(
                    timdex.Holding(
                        collection=holding_collection_value or None,
                        format="electronic resource",
                        location=holding_location_value or None,
                        note=holding_note_value or None,
                    )
                )
        for datafield in xml.find_all("datafield", tag="987"):
            from_year = self.create_subfield_value_string_from_datafield(
                datafield, "b", ", "
            )
            from_month = self.create_subfield_value_string_from_datafield(
                datafield, "c", ", "
            )
            from_day = self.create_subfield_value_string_from_datafield(
                datafield, "d", ", "
            )
            from_volume = self.create_subfield_value_string_from_datafield(
                datafield, "e", ", "
            )
            from_issue = self.create_subfield_value_string_from_datafield(
                datafield, "f", ", "
            )
            to_year = self.create_subfield_value_string_from_datafield(
                datafield, ["bb"], ", "
            )
            to_month = self.create_subfield_value_string_from_datafield(
                datafield, ["cc"], ", "
            )
            to_day = self.create_subfield_value_string_from_datafield(
                datafield, ["dd"], ", "
            )
            to_volume = self.create_subfield_value_string_from_datafield(
                datafield, ["ee"], ", "
            )
            to_issue = self.create_subfield_value_string_from_datafield(
                datafield, ["ff"], ", "
            )
            serial_holding_note_value = ""
            if from_year or from_month or from_day or from_volume or from_issue:
                serial_holding_note_value += "From:"
                if not from_year:
                    from_year = "XXXX"
                if not from_month:
                    from_month = "XX"
                if not from_day:
                    from_day = "XX"
                serial_holding_note_value += f" {from_year}-{from_month}-{from_day}"
                if from_volume:
                    serial_holding_note_value += f" Vol. {from_volume}"
                if from_issue:
                    serial_holding_note_value += f" Issue {from_issue}"
            if to_year or to_month or to_day or to_volume or to_issue:
                serial_holding_note_value += ", To:"
                if not to_year:
                    to_year = "XXXX"
                if not to_month:
                    to_month = "XX"
                if not to_day:
                    to_day = "XX"
                serial_holding_note_value += f" {to_year}-{to_month}-{to_day}"
                if to_volume:
                    serial_holding_note_value += f" Vol. {to_volume}"
                if to_issue:
                    serial_holding_note_value += f" Issue {to_issue}"
            if serial_holding_note_value:
                fields.setdefault("holdings", []).append(
                    timdex.Holding(
                        note=serial_holding_note_value or None,
                    )
                )

        # identifiers
        identifier_marc_fields = [
            {
                "tag": "010",
                "subfields": "a",
                "kind": "LCCN",
            },
            {
                "tag": "020",
                "subfields": "aq",
                "kind": "ISBN",
            },
            {
                "tag": "022",
                "subfields": "a",
                "kind": "ISSN",
            },
            {
                "tag": "024",
                "subfields": "aq2",
                "kind": "Other Identifier",
            },
            {
                "tag": "035",
                "subfields": "a",
                "kind": "OCLC Number",
            },
        ]
        for identifier_marc_field in identifier_marc_fields:
            for datafield in xml.find_all(
                "datafield", tag=identifier_marc_field["tag"]
            ):
                if identifier_value := (
                    self.create_subfield_value_string_from_datafield(
                        datafield,
                        identifier_marc_field["subfields"],
                        ". ",
                    )
                ):
                    fields.setdefault("identifiers", []).append(
                        timdex.Identifier(
                            value=identifier_value.strip().replace("(OCoLC)", ""),
                            kind=identifier_marc_field["kind"],
                        )
                    )

        # languages
        languages = []

        # Get language codes
        language_codes = []
        if fixed_length_data:
            if fixed_language_value := fixed_length_data.string[35:38]:
                language_codes.append(fixed_language_value)
        for field_041 in xml.find_all("datafield", tag="041"):
            language_codes.extend(
                self.create_subfield_value_list_from_datafield(field_041, "abdefghjkmn")
            )

        # Crosswalk codes to names
        for language_code in list(dict.fromkeys(language_codes)):
            if language_name := Marc.loc_crosswalk_code_to_name(
                language_code, language_code_crosswalk, record_id, "language"
            ):
                languages.append(language_name)

        # Add language notes
        for field_546 in xml.find_all("datafield", tag="546"):
            if language_note := field_546.find("subfield", code="a", string=True):
                languages.append(language_note.string.rstrip(" ."))

        fields["languages"] = list(dict.fromkeys(languages)) or None

        # links
        # If indicator 1 is 4 and indicator 2 is 0 or 1, take the URL from subfield u,
        # the kind from subfield 3, link text from subfield y, and restrictions from
        # subfield z."
        for datafield in xml.find_all(
            "datafield", tag="856", ind1="4", ind2=["0", "1"]
        ):
            url_value = self.create_subfield_value_list_from_datafield(datafield, "u")
            text_value = self.create_subfield_value_list_from_datafield(datafield, "y")
            restrictions_value = self.create_subfield_value_list_from_datafield(
                datafield, "z"
            )
            if kind_value := datafield.find("subfield", code="3", string=True):
                kind_value = kind_value.string
            if url_value:
                fields.setdefault("links", []).append(
                    timdex.Link(
                        url=". ".join(url_value),
                        kind=kind_value or "Digital object URL",
                        restrictions=". ".join(restrictions_value) or None,
                        text=". ".join(text_value) or None,
                    )
                )

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

        # Get place of publication from 008 field code
        if fixed_length_data:
            if fixed_location_code := fixed_length_data.string[15:17]:
                if location_name := Marc.loc_crosswalk_code_to_name(
                    fixed_location_code, country_code_crosswalk, record_id, "country"
                ):
                    fields.setdefault("locations", []).append(
                        timdex.Location(
                            value=location_name, kind="Place of Publication"
                        )
                    )

        # Get other locations
        location_marc_fields = [
            {
                "tag": "751",
                "subfields": "a",
                "kind": "Geographic Name",
            },
            {
                "tag": "752",
                "subfields": "abcdefgh",
                "kind": "Hierarchical Place Name",
            },
        ]
        for location_marc_field in location_marc_fields:
            for datafield in xml.find_all("datafield", tag=location_marc_field["tag"]):
                if location_value := (
                    self.create_subfield_value_string_from_datafield(
                        datafield,
                        location_marc_field["subfields"],
                        " - ",
                    )
                ):
                    fields.setdefault("locations", []).append(
                        timdex.Location(
                            value=location_value.rstrip(" .,/)"),
                            kind=location_marc_field["kind"],
                        )
                    )

        # notes
        note_marc_fields = [
            {
                "tag": "245",
                "subfields": "c",
                "kind": "Title Statement of Responsibility",
            },
            {
                "tag": "500",
                "subfields": "a",
                "kind": "General Note",
            },
            {
                "tag": "502",
                "subfields": "abcdg",
                "kind": "Dissertation Note",
            },
            {
                "tag": "504",
                "subfields": "a",
                "kind": "Bibliography Note",
            },
            {
                "tag": "508",
                "subfields": "a",
                "kind": "Creation/Production Credits Note",
            },
            {
                "tag": "511",
                "subfields": "a",
                "kind": "Participant or Performer Note",
            },
            {
                "tag": "515",
                "subfields": "a",
                "kind": "Numbering Peculiarities Note",
            },
            {
                "tag": "522",
                "subfields": "a",
                "kind": "Geographic Coverage Note",
            },
            {
                "tag": "533",
                "subfields": "abcdefmn",
                "kind": "Reproduction Note",
            },
            {
                "tag": "534",
                "subfields": "abcefklmnoptxz",
                "kind": "Original Version Note",
            },
            {
                "tag": "588",
                "subfields": "a",
                "kind": "Source of Description Note",
            },
            {
                "tag": "590",
                "subfields": "a",
                "kind": "Local Note",
            },
        ]
        for note_marc_field in note_marc_fields:
            for datafield in xml.find_all("datafield", tag=note_marc_field["tag"]):
                if note_value := (
                    self.create_subfield_value_string_from_datafield(
                        datafield,
                        note_marc_field["subfields"],
                        " ",
                    )
                ):
                    fields.setdefault("notes", []).append(
                        timdex.Note(
                            value=[note_value.rstrip(" .")],
                            kind=note_marc_field["kind"],
                        )
                    )

        # numbering
        numbering_values = []
        for datafield in xml.find_all("datafield", tag="362"):
            if numbering_value := self.create_subfield_value_string_from_datafield(
                datafield, "a", " "
            ):
                numbering_values.append(numbering_value)
        fields["numbering"] = " ".join(numbering_values) or None

        # physical_description
        physical_description_values = []
        for datafield in xml.find_all("datafield", tag="300"):
            if physical_description_value := (
                self.create_subfield_value_string_from_datafield(
                    datafield, "abcefg", " "
                )
            ):
                physical_description_values.append(physical_description_value)
        fields["physical_description"] = " ".join(physical_description_values) or None

        # publication_frequency
        for datafield in xml.find_all("datafield", tag="310"):
            if publication_frequency_value := (
                self.create_subfield_value_string_from_datafield(datafield, "a", " ")
            ):
                fields.setdefault("publication_frequency", []).append(
                    publication_frequency_value
                )

        # publication_information
        publication_information_marc_fields = [
            {
                "tag": "260",
                "subfields": "abcdef",
            },
            {
                "tag": "264",
                "subfields": "abc",
            },
        ]
        for publication_information_marc_field in publication_information_marc_fields:
            for datafield in xml.find_all(
                "datafield", tag=publication_information_marc_field["tag"]
            ):
                if publication_information_value := (
                    self.create_subfield_value_string_from_datafield(
                        datafield, publication_information_marc_field["subfields"], " "
                    )
                ):
                    fields.setdefault("publication_information", []).append(
                        publication_information_value.rstrip(" .")
                    )

        # related_items
        related_item_marc_fields = [
            {
                "tag": "765",
                "subfields": "abcdghikmnorstuwxyz",
                "relationship": "Original Language Version",
            },
            {
                "tag": "770",
                "subfields": "abcdghikmnorstuwxyz",
                "relationship": "Has Supplement",
            },
            {
                "tag": "772",
                "subfields": "abcdghikmnorstuwxyz",
                "relationship": "Supplement To",
            },
            {
                "tag": "780",
                "subfields": "abcdghikmnorstuwxyz",
                "relationship": "Previous Title",
            },
            {
                "tag": "785",
                "subfields": "abcdghikmnorstuwxyz",
                "relationship": "Subsequent Title",
            },
            {
                "tag": "787",
                "subfields": "abcdghikmnorstuwxyz",
                "relationship": "Not Specified",
            },
            {
                "tag": "830",
                "subfields": "adfghklmnoprstvwx",
                "relationship": "In Series",
            },
            {
                "tag": "510",
                "subfields": "abcx",
                "relationship": "In Bibliography",
            },
        ]
        for related_item_marc_field in related_item_marc_fields:
            for datafield in xml.find_all(
                "datafield", tag=related_item_marc_field["tag"]
            ):
                if related_item_value := (
                    self.create_subfield_value_string_from_datafield(
                        datafield,
                        related_item_marc_field["subfields"],
                        " ",
                    )
                ):
                    fields.setdefault("related_items", []).append(
                        timdex.RelatedItem(
                            description=related_item_value.rstrip(" ."),
                            relationship=related_item_marc_field["relationship"],
                        )
                    )

        # rights not used in MARC

        # subjects
        subject_marc_fields = [
            {
                "tag": "600",
                "subfields": "abcdefghjklmnopqrstuvxyz",
                "kind": "Personal Name",
            },
            {
                "tag": "610",
                "subfields": "abcdefghklmnoprstuvxyz",
                "kind": "Corporate Name",
            },
            {
                "tag": "650",
                "subfields": "avxyz",
                "kind": "Topical Term",
            },
            {
                "tag": "651",
                "subfields": "avxyz",
                "kind": "Geographic Name",
            },
        ]
        for subject_marc_field in subject_marc_fields:
            for datafield in xml.find_all("datafield", tag=subject_marc_field["tag"]):
                if subject_value := (
                    self.create_subfield_value_string_from_datafield(
                        datafield,
                        subject_marc_field["subfields"],
                        " - ",
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
        subfield_codes: Union[list, str],
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
        subfield_codes: Union[list, str],
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
    def loc_crosswalk_code_to_name(
        code: str, crosswalk: Tag, record_id: str, code_type: str
    ) -> Optional[str]:
        """
        Retrieve the name associated with a given code from a Library of Congress XML
        code crosswalk. Logs a warning and returns None if the code isn't found in the
        crosswalk. Logs a warning and returns the name if the code is obsolete.

        Args:
            code: The code from a MARC record.
            crosswalk: The crosswalked bs4 Tag to use, loaded from a config file.
            record_id: The MMS ID of the MARC record.
            code_type: The type of code, e.g. country or language.
        """
        code_element = crosswalk.find("code", string=code)
        if code_element is None:
            logger.warning(
                "Record #%s uses an invalid %s code: %s", record_id, code_type, code
            )
            return None
        if code_element.get("status") == "obsolete":
            logger.warning(
                "Record #%s uses an obsolete %s code: %s", record_id, code_type, code
            )
        return str(code_element.parent.find("name").string)

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
