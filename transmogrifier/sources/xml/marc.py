import logging

from bs4 import Tag  # type: ignore[import-untyped]

import transmogrifier.models as timdex
from transmogrifier.config import load_external_config
from transmogrifier.exceptions import SkippedRecordEvent
from transmogrifier.helpers import validate_date
from transmogrifier.sources.xmltransformer import XMLTransformer

logger = logging.getLogger(__name__)


class Marc(XMLTransformer):
    """Marc transformer."""

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

    def get_optional_fields(self, source_record: Tag) -> dict | None:
        """
        Retrieve optional TIMDEX fields from a MARC XML record.

        Overrides metaclass get_optional_fields() method.

        Args:
            source_record: A BeautifulSoup Tag representing a single MARC XML record.
        """
        fields: dict = {}

        source_record_id = self.get_source_record_id(source_record)

        # alternate titles
        fields["alternate_titles"] = self.get_alternate_titles(source_record)

        # call_numbers
        fields["call_numbers"] = self.get_call_numbers(source_record)

        # citation not used in MARC

        # content_type
        if content_type := Marc.json_crosswalk_code_to_name(
            self._get_leader_field(source_record)[6:7],
            self.marc_content_type_crosswalk,
            source_record_id,
            "Leader/06",
        ):
            fields["content_type"] = [content_type]

        # contents
        for datafield in source_record.find_all("datafield", tag="505"):
            for contents_value in self.create_subfield_value_list_from_datafield(
                datafield,
                "agrt",
            ):
                for contents_item in contents_value.split(" -- "):
                    fields.setdefault("contents", []).append(contents_item.rstrip(" ./-"))

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
            for datafield in source_record.find_all(
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
        publication_year = self._get_control_field(source_record)[7:11].strip()
        if validate_date(publication_year, source_record_id):
            fields["dates"] = [
                timdex.Date(kind="Publication date", value=publication_year)
            ]

        # edition
        edition_values = []
        for datafield in source_record.find_all("datafield", tag="250"):
            if edition_value := self.create_subfield_value_string_from_datafield(
                datafield, "ab", " "
            ):
                edition_values.append(edition_value)  # noqa: PERF401
        fields["edition"] = " ".join(edition_values) or None

        # file_formats

        # format

        # funding_information

        # holdings
        # physical items
        for datafield in source_record.find_all("datafield", tag="985"):
            holding_call_number_value = self.create_subfield_value_string_from_datafield(
                datafield, ["bb"]
            )
            holding_collection_value = Marc.json_crosswalk_code_to_name(
                self.create_subfield_value_string_from_datafield(datafield, ["aa"]),
                self.holdings_collection_crosswalk,
                source_record_id,
                "985 $aa",
            )
            holding_format_value = Marc.json_crosswalk_code_to_name(
                self.create_subfield_value_string_from_datafield(datafield, "t"),
                self.holdings_format_crosswalk,
                source_record_id,
                "985 $t",
            )
            holding_location_value = Marc.json_crosswalk_code_to_name(
                self.create_subfield_value_string_from_datafield(datafield, "i"),
                self.holdings_location_crosswalk,
                source_record_id,
                "985 $i",
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
        # electronic portfolio items
        for field_986 in source_record.find_all("datafield", tag="986"):
            electronic_item_collection = self.get_single_subfield_string(field_986, "j")
            electronic_item_location = (
                self.get_single_subfield_string(field_986, "f")
                or self.get_single_subfield_string(field_986, "l")
                or self.get_single_subfield_string(field_986, "d")
            )
            electronic_item_note = self.get_single_subfield_string(field_986, "i")
            if any(
                [
                    electronic_item_collection,
                    electronic_item_location,
                    electronic_item_note,
                ]
            ):
                fields.setdefault("holdings", []).append(
                    timdex.Holding(
                        collection=electronic_item_collection,
                        format="electronic resource",
                        location=electronic_item_location,
                        note=electronic_item_note,
                    )
                )
            # If there's a URL, add to links field as well
            if electronic_item_location:
                fields.setdefault("links", []).append(
                    timdex.Link(
                        url=electronic_item_location,
                        kind="Digital object URL",
                        text=electronic_item_collection,
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
            for datafield in source_record.find_all(
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
        if fixed_language_value := self._get_control_field(source_record)[35:38]:
            language_codes.append(fixed_language_value)
        for field_041 in source_record.find_all("datafield", tag="041"):
            language_codes.extend(
                self.create_subfield_value_list_from_datafield(field_041, "abdefghjkmn")
            )

        # Crosswalk codes to names
        for language_code in list(dict.fromkeys(language_codes)):
            if language_name := Marc.loc_crosswalk_code_to_name(
                language_code, self.language_code_crosswalk, source_record_id, "language"
            ):
                languages.append(language_name)  # noqa: PERF401

        # Add language notes
        for field_546 in source_record.find_all("datafield", tag="546"):
            if language_note := field_546.find("subfield", code="a", string=True):
                languages.append(str(language_note.string).rstrip(" ."))  # noqa: PERF401

        fields["languages"] = list(dict.fromkeys(languages)) or None

        # links - see also: holdings field for electronic portfolio items
        # If indicator 1 is 4 and indicator 2 is 0 or 1, take the URL from subfield u,
        # the kind from subfield 3, link text from subfield y, and restrictions from
        # subfield z."
        for datafield in source_record.find_all(
            "datafield", tag="856", ind1="4", ind2=["0", "1"]
        ):
            url_value = self.create_subfield_value_list_from_datafield(datafield, "u")
            text_value = self.create_subfield_value_list_from_datafield(datafield, "y")
            restrictions_value = self.create_subfield_value_list_from_datafield(
                datafield, "z"
            )
            if kind_value := datafield.find("subfield", code="3", string=True):
                kind_value = str(kind_value.string)
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
        if (
            self._get_leader_field(source_record)[6:7] in "at"
            and self._get_leader_field(source_record)[7:8] in "acdm"
        ):
            if self._get_control_field(source_record)[33:34] in "0se":
                fields["literary_form"] = "Nonfiction"
            elif self._get_control_field(source_record)[33:34]:
                fields["literary_form"] = "Fiction"

        # locations

        # Get place of publication from 008 field code
        if (fixed_location_code := self._get_control_field(source_record)[15:17]) and (
            location_name := Marc.loc_crosswalk_code_to_name(
                fixed_location_code,
                self.country_code_crosswalk,
                source_record_id,
                "country",
            )
        ):
            fields.setdefault("locations", []).append(
                timdex.Location(value=location_name, kind="Place of Publication")
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
            for datafield in source_record.find_all(
                "datafield", tag=location_marc_field["tag"]
            ):
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
            for datafield in source_record.find_all(
                "datafield", tag=note_marc_field["tag"]
            ):
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

        if numbering_values := [
            self.create_subfield_value_string_from_datafield(datafield, "a", " ")
            for datafield in source_record.find_all("datafield", tag="362")
        ]:
            fields["numbering"] = " ".join(numbering_values) or None

        # physical_description
        if physical_description_values := [
            self.create_subfield_value_string_from_datafield(datafield, "abcefg", " ")
            for datafield in source_record.find_all("datafield", tag="300")
        ]:
            fields["physical_description"] = " ".join(physical_description_values) or None

        # publication_frequency
        for datafield in source_record.find_all("datafield", tag="310"):
            if publication_frequency_value := (
                self.create_subfield_value_string_from_datafield(datafield, "a", " ")
            ):
                fields.setdefault("publication_frequency", []).append(
                    publication_frequency_value
                )

        # publishers
        for publisher_marc_field in ["260", "264"]:
            for datafield in source_record.find_all(
                "datafield", tag=publisher_marc_field
            ):
                publisher_name = self.get_single_subfield_string(datafield, "b")
                publisher_date = self.get_single_subfield_string(datafield, "c")
                publisher_location = self.get_single_subfield_string(datafield, "a")
                if any([publisher_name, publisher_date, publisher_location]):
                    fields.setdefault("publishers", []).append(
                        timdex.Publisher(
                            name=publisher_name.rstrip(",") if publisher_name else None,
                            date=publisher_date.rstrip(".") if publisher_date else None,
                            location=(
                                publisher_location.rstrip(" :")
                                if publisher_location
                                else None
                            ),
                        )
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
            for datafield in source_record.find_all(
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
            for datafield in source_record.find_all(
                "datafield", tag=subject_marc_field["tag"]
            ):
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
        for datafield in source_record.find_all("datafield", tag="520"):
            if summary_value := self.create_subfield_value_string_from_datafield(
                datafield, "a", " "
            ):
                fields.setdefault("summary", []).append(summary_value)

        return fields

    @staticmethod
    def create_subfield_value_list_from_datafield(
        xml_element: Tag,
        subfield_codes: list | str,
    ) -> list:
        """
        Create a list of values from the specified subfields of a
        datafield element.

        Args:
            xml_element: A BeautifulSoup Tag representing a single MARC XML element.
            subfield_codes: The codes of the subfields to extract.
        """
        return [
            str(subfield.string)
            for subfield in xml_element.find_all(name=True, string=True)
            if subfield.get("code", "") in subfield_codes
        ]

    @staticmethod
    def create_subfield_value_string_from_datafield(
        xml_element: Tag,
        subfield_codes: list | str,
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
    def get_single_subfield_string(xml_element: Tag, subfield_code: str) -> str | None:
        """
        Get the string value of a <subfield> element with specified code(s).

        Finds and returns the string value of a single <subfield> element if the
        element contains a string. This uses bs4's find() method and thus will return
        only the string value from the first <subfield> element matching the criteria.

        Returns None if no matching <subfield> element containing a string is found, or
        if the matching element's string value is only whitespace.

        Args:
            xml_element: A BeautifulSoup Tag representing a single MARC XML element.
            subfield_code: The code attribute of the subfields to extract.
        """
        if subfield := xml_element.find("subfield", code=subfield_code, string=True):
            return str(subfield.string).strip() or None
        return None

    @staticmethod
    def json_crosswalk_code_to_name(
        code: str, crosswalk: dict, record_id: str, field_name: str
    ) -> str | None:
        """
        Retrieve the name associated with a given code from a JSON crosswalk. Logs a
        message and returns None if the code isn't found in the crosswalk.

        Args:
            code: The code from a MARC record.
            crosswalk: The crosswalk dict to use, loaded from a config file.
            record_id: The MMS ID of the MARC record.
            field_name: The MARC field containing the code.
        """
        name = crosswalk.get(code)
        if name is None:
            logger.debug(
                "Record #%s uses an invalid code in %s: %s", record_id, field_name, code
            )
            return None
        return name

    @staticmethod
    def loc_crosswalk_code_to_name(
        code: str, crosswalk: Tag, record_id: str, code_type: str
    ) -> str | None:
        """
        Retrieve the name associated with a given code from a Library of Congress XML
        code crosswalk. Logs a message and returns None if the code isn't found in the
        crosswalk. Logs a message and returns the name if the code is obsolete.

        Args:
            code: The code from a MARC record.
            crosswalk: The crosswalked bs4 Tag to use, loaded from a config file.
            record_id: The MMS ID of the MARC record.
            code_type: The type of code, e.g. country or language.
        """
        code_element = crosswalk.find("code", string=code)
        if code_element is None:
            logger.debug(
                "Record #%s uses an invalid %s code: %s", record_id, code_type, code
            )
            return None
        if code_element.get("status") == "obsolete":
            logger.debug(
                "Record #%s uses an obsolete %s code: %s", record_id, code_type, code
            )
        return str(code_element.parent.find("name").string)

    @classmethod
    def _get_leader_field(cls, source_record: Tag) -> str:
        if leader := source_record.find("leader", string=True):
            return str(leader.string)
        message = "Record skipped because key information is missing: <leader>."
        raise SkippedRecordEvent(message)

    @classmethod
    def _get_control_field(cls, source_record: Tag) -> str:
        if control_field := source_record.find("controlfield", tag="008", string=True):
            return str(control_field.string)
        message = (
            "Record skipped because key information is missing: "
            '<controlfield tag="008">.'
        )
        raise SkippedRecordEvent(message)

    @classmethod
    def get_alternate_titles(
        cls, source_record: Tag
    ) -> list[timdex.AlternateTitle] | None:
        alternate_titles = []
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
            alternate_titles.extend(
                [
                    timdex.AlternateTitle(
                        value=alternate_title_value.rstrip(" .,/"),
                        kind=alternate_title_marc_field["kind"],
                    )
                    for datafield in source_record.find_all(
                        "datafield", tag=alternate_title_marc_field["tag"]
                    )
                    if (
                        alternate_title_value := (
                            cls.create_subfield_value_string_from_datafield(
                                datafield,
                                alternate_title_marc_field["subfields"],
                                " ",
                            )
                        )
                    )
                ]
            )
        return alternate_titles or None

    @classmethod
    def get_call_numbers(cls, source_record: Tag) -> list[str] | None:
        call_numbers: list = []
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
            for datafield in source_record.find_all(
                "datafield", tag=call_number_marc_field["tag"]
            ):
                call_numbers.extend(
                    call_number
                    for call_number in cls.create_subfield_value_list_from_datafield(
                        datafield, call_number_marc_field["subfields"]
                    )
                )
        return call_numbers or None

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
        except AttributeError:
            logger.exception(
                "Record ID %s is missing a 245 field", Marc.get_source_record_id(xml)
            )
            return []
        else:
            return main_title_values

    @staticmethod
    def get_source_record_id(xml: Tag) -> str:
        """
        Get the source record ID from a MARC XML record.

        Overrides metaclass get_source_record_id() method.

        Args:
            xml: A BeautifulSoup Tag representing a single MARC XML record.
        """
        return str(xml.find("controlfield", tag="001", string=True).string)

    @classmethod
    def record_is_deleted(cls, xml: Tag) -> bool:
        """
        Determine whether record has a status of deleted.

        Overrides metaclass record_is_deleted() method.

        Args:
            xml: A BeautifulSoup Tag representing a single MARC XML record
        """
        if leader := xml.find("leader", string=True):  # noqa: SIM102
            if leader.string[5:6] == "d":
                return True
        return False
