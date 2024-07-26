import logging
from collections import defaultdict
from collections.abc import Iterator

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

        # alternate titles
        fields["alternate_titles"] = self.get_alternate_titles(source_record)

        # call_numbers
        fields["call_numbers"] = self.get_call_numbers(source_record)

        # citation not used in MARC

        # content_type
        fields["content_type"] = self.get_content_type(source_record)

        # contents
        fields["contents"] = self.get_contents(source_record)

        # contributors
        fields["contributors"] = self.get_contributors(source_record)

        # dates
        fields["dates"] = self.get_dates(source_record)

        # edition
        fields["edition"] = self.get_edition(source_record)

        # file_formats

        # format

        # funding_information

        # holdings
        fields["holdings"] = self.get_holdings(source_record)

        # identifiers
        fields["identifiers"] = self.get_identifiers(source_record)

        # languages
        fields["languages"] = self.get_languages(source_record)

        # links - see also: holdings field for electronic portfolio items
        fields["links"] = self.get_links(source_record)

        # literary_form
        fields["literary_form"] = self.get_literary_form(source_record)

        # locations
        fields["locations"] = self.get_locations(source_record)

        # notes
        fields["notes"] = self.get_notes(source_record)

        # numbering
        fields["numbering"] = self.get_numbering(source_record)

        # physical_description
        fields["physical_description"] = self.get_physical_description(source_record)

        # publication_frequency
        fields["publication_frequency"] = self.get_publication_frequency(source_record)

        # publishers
        fields["publishers"] = self.get_publishers(source_record)

        # related_items
        fields["related_items"] = self.get_related_items(source_record)

        # rights not used in MARC

        # subjects
        fields["subjects"] = self.get_subjects(source_record)

        # summary
        fields["summary"] = self.get_summary(source_record)
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

    @classmethod
    def concatenate_subfield_value_strings_from_datafield(
        cls, source_record: Tag, tag: str, subfield_codes: str
    ) -> str:
        return " ".join(
            cls.create_subfield_value_string_from_datafield(
                datafield, subfield_codes, " "
            )
            for datafield in source_record.find_all("datafield", tag=tag)
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

    @classmethod
    def get_content_type(cls, source_record: Tag) -> list[str] | None:
        if content_type := cls.json_crosswalk_code_to_name(
            code=cls._get_leader_field(source_record)[6:7],
            crosswalk=cls.marc_content_type_crosswalk,
            record_id=cls.get_source_record_id(source_record),
            field_name="Leader/06",
        ):
            return [content_type]
        return None

    @classmethod
    def get_contents(cls, source_record: Tag) -> list[str] | None:
        contents = []
        for datafield in source_record.find_all("datafield", tag="505"):
            for contents_value in cls.create_subfield_value_list_from_datafield(
                datafield,
                "agrt",
            ):
                contents.extend(
                    [
                        contents_item.rstrip(" ./-")
                        for contents_item in contents_value.split(" -- ")
                    ]
                )
        return contents or None

    @classmethod
    def get_contributors(cls, source_record: Tag) -> list[timdex.Contributor] | None:
        """Retrieve contributors using data from relevant MARC fields.

        The method starts by creating a dictionary where the keys are
        contributor names and the values are a set of unique 'kind' values
        retrieved from the MARC record (subfield code 'e'). When the value
        is an empty set, this means that subfield code 'e' was blank or
        missing from the record.

        Using the dictionary, the method will create model.Contributor
        instances for every unique 'kind' value associated with a
        contributor name. When the value (in the dictionary) is an empty
        set, the created instance will set kind="Not specified".
        """
        contributors: list = []
        contributors_dict = defaultdict(set)
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
            for datafield in source_record.find_all(
                "datafield", tag=contributor_marc_field["tag"]
            ):
                if contributor_name := (
                    cls.create_subfield_value_string_from_datafield(
                        datafield,
                        contributor_marc_field["subfields"],
                        " ",
                    )
                ):
                    contributor_name = contributor_name.rstrip(" .,")
                    contributor_kinds = cls.create_subfield_value_list_from_datafield(
                        datafield, "e"
                    )
                    contributors_dict[contributor_name].update(contributor_kinds)

        for name, kinds in contributors_dict.items():
            if len(kinds) == 0:
                contributors.append(timdex.Contributor(value=name, kind="Not specified"))
            else:
                contributors.extend(
                    [
                        timdex.Contributor(value=name, kind=kind.strip(" .,"))
                        for kind in sorted(kinds, key=lambda k: k.lower())
                    ]
                )
        return contributors or None

    @classmethod
    def get_dates(cls, source_record: Tag) -> list[timdex.Date] | None:
        publication_year = cls._get_control_field(source_record)[7:11].strip()
        if validate_date(publication_year, cls.get_source_record_id(source_record)):
            return [timdex.Date(kind="Publication date", value=publication_year)]
        return None

    @classmethod
    def get_edition(cls, source_record: Tag) -> str | None:
        edition_values = [
            edition_value
            for datafield in source_record.find_all("datafield", tag="250")
            if (
                edition_value := cls.create_subfield_value_string_from_datafield(
                    datafield, "ab", " "
                )
            )
        ]
        return " ".join(edition_values) or None

    @classmethod
    def get_holdings(cls, source_record: Tag) -> list[timdex.Holding] | None:
        holdings: list[timdex.Holding] = []
        holdings.extend(cls._get_holdings_physical_items(source_record))
        holdings.extend(cls._get_holdings_electronic_items(source_record))
        return holdings or None

    @classmethod
    def _get_holdings_physical_items(cls, source_record: Tag) -> Iterator[timdex.Holding]:
        for datafield in source_record.find_all("datafield", tag="985"):
            holding_call_number = cls.create_subfield_value_string_from_datafield(
                datafield, ["bb"]
            )
            holding_collection = cls.json_crosswalk_code_to_name(
                code=cls.create_subfield_value_string_from_datafield(datafield, ["aa"]),
                crosswalk=cls.holdings_collection_crosswalk,
                record_id=cls.get_source_record_id(source_record),
                field_name="985 $aa",
            )
            holding_format = cls.json_crosswalk_code_to_name(
                code=cls.create_subfield_value_string_from_datafield(datafield, "t"),
                crosswalk=cls.holdings_format_crosswalk,
                record_id=cls.get_source_record_id(source_record),
                field_name="985 $t",
            )
            holding_location = cls.json_crosswalk_code_to_name(
                code=cls.create_subfield_value_string_from_datafield(datafield, "i"),
                crosswalk=cls.holdings_location_crosswalk,
                record_id=cls.get_source_record_id(source_record),
                field_name="985 $i",
            )
            holding_note = cls.create_subfield_value_string_from_datafield(
                datafield, "g", ", "
            )
            if any(
                [
                    holding_call_number,
                    holding_collection,
                    holding_format,
                    holding_location,
                    holding_note,
                ]
            ):
                yield timdex.Holding(
                    call_number=holding_call_number or None,
                    collection=holding_collection or None,
                    format=holding_format or None,
                    location=holding_location or None,
                    note=holding_note or None,
                )

    @classmethod
    def _get_holdings_electronic_items(
        cls, source_record: Tag
    ) -> Iterator[timdex.Holding]:
        for datafield in source_record.find_all("datafield", tag="986"):
            holding_collection = cls.get_single_subfield_string(datafield, "j")
            holding_location = (
                cls.get_single_subfield_string(datafield, "f")
                or cls.get_single_subfield_string(datafield, "l")
                or cls.get_single_subfield_string(datafield, "d")
            )
            holding_note = cls.get_single_subfield_string(datafield, "i")
            if any(
                [
                    holding_collection,
                    holding_location,
                    holding_note,
                ]
            ):
                yield timdex.Holding(
                    collection=holding_collection,
                    format="electronic resource",
                    location=holding_location,
                    note=holding_note,
                )

    @classmethod
    def get_identifiers(cls, source_record: Tag) -> list[timdex.Identifier] | None:
        identifiers = []
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
            identifiers.extend(
                [
                    timdex.Identifier(
                        value=identifier.strip().replace("(OCoLC)", ""),
                        kind=identifier_marc_field["kind"],
                    )
                    for datafield in source_record.find_all(
                        "datafield", tag=identifier_marc_field["tag"]
                    )
                    if (
                        identifier := (
                            cls.create_subfield_value_string_from_datafield(
                                datafield,
                                identifier_marc_field["subfields"],
                                ". ",
                            )
                        )
                    )
                ]
            )
        return identifiers or None

    @classmethod
    def get_languages(cls, source_record: Tag) -> list[str] | None:

        languages = []
        language_codes: list[str] = []

        # get language codes from control field 008/35-37
        if fixed_language_value := cls._get_control_field(source_record)[35:38].strip():
            language_codes.append(fixed_language_value)

        # get language codes from data field 041
        for datafield in source_record.find_all("datafield", tag="041"):
            language_codes.extend(
                cls.create_subfield_value_list_from_datafield(datafield, "abdefghjkmn")
            )

        languages.extend(cls._get_language_names(source_record, language_codes))
        languages.extend(cls._get_language_notes(source_record))
        return languages or None

    @classmethod
    def _get_language_names(
        cls, source_record: Tag, language_codes: list[str]
    ) -> list[str]:
        return [
            language_name
            for language_code in list(dict.fromkeys(language_codes))
            if (
                language_name := cls.loc_crosswalk_code_to_name(
                    language_code,
                    cls.language_code_crosswalk,
                    cls.get_source_record_id(source_record),
                    "language",
                )
            )
        ]

    @classmethod
    def _get_language_notes(cls, source_record: Tag) -> list[str]:
        return [
            str(language_note.string).rstrip(" .")
            for datafield in source_record.find_all("datafield", tag="546")
            if (language_note := datafield.find("subfield", code="a", string=True))
        ]

    @classmethod
    def get_links(cls, source_record: Tag) -> list[timdex.Link] | None:
        links: list[timdex.Link] = []
        for datafield in source_record.find_all(
            "datafield", tag="856", ind1="4", ind2=["0", "1"]
        ):
            url_value = cls.create_subfield_value_list_from_datafield(datafield, "u")
            text_value = cls.create_subfield_value_list_from_datafield(datafield, "y")
            restrictions_value = cls.create_subfield_value_list_from_datafield(
                datafield, "z"
            )
            if kind_value := datafield.find("subfield", code="3", string=True):
                kind_value = str(kind_value.string)
            if url_value:
                links.append(
                    timdex.Link(
                        url=". ".join(url_value),
                        kind=kind_value or "Digital object URL",
                        restrictions=". ".join(restrictions_value) or None,
                        text=". ".join(text_value) or None,
                    )
                )

        # get links from 'electronic item' holdings
        links.extend(cls._get_links_holdings_electronic_items(source_record))
        return links or None

    @classmethod
    def _get_links_holdings_electronic_items(
        cls, source_record: Tag
    ) -> Iterator[timdex.Link]:
        for datafield in source_record.find_all("datafield", tag="986"):
            holding_collection = cls.get_single_subfield_string(datafield, "j")
            holding_location = (
                cls.get_single_subfield_string(datafield, "f")
                or cls.get_single_subfield_string(datafield, "l")
                or cls.get_single_subfield_string(datafield, "d")
            )
            if holding_location:
                yield timdex.Link(
                    url=holding_location,
                    kind="Digital object URL",
                    text=holding_collection,
                )

    @classmethod
    def get_literary_form(cls, source_record: Tag) -> str | None:
        """Retrieve literary form for book materials.

        Book materials configurations are used when Leader/06 (Type of record)
        contains code a (Language material) or t (Manuscript language material)
        and Leader/07 (Bibliographic level) contains code
        a (Monographic component part), c (Collection), d (Subunit),
        or m (Monograph).
        """
        leader_field = cls._get_leader_field(source_record)
        control_field = cls._get_control_field(source_record)
        if leader_field[6] in "at" and leader_field[7] in "acdm":
            if control_field[33] in "0se":
                return "Nonfiction"
            return "Fiction"
        return None

    @classmethod
    def get_locations(cls, source_record: Tag) -> list[timdex.Location] | None:
        locations = []
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
        # get locations (place of publication) from control field 008/15-17
        if place_of_publication := cls._get_location_publication(source_record):
            locations.append(place_of_publication)

        # get locations from data fields
        for location_marc_field in location_marc_fields:
            locations.extend(
                [
                    timdex.Location(
                        value=location_value.rstrip(" .,/)"),
                        kind=location_marc_field["kind"],
                    )
                    for datafield in source_record.find_all(
                        "datafield", tag=location_marc_field["tag"]
                    )
                    if (
                        location_value := (
                            cls.create_subfield_value_string_from_datafield(
                                datafield,
                                location_marc_field["subfields"],
                                " - ",
                            )
                        )
                    )
                ]
            )
        return locations or None

    @classmethod
    def _get_location_publication(cls, source_record: Tag) -> timdex.Location | None:
        if (
            fixed_location_code := cls._get_control_field(source_record)[15:18].strip()
        ) and (
            location_name := cls.loc_crosswalk_code_to_name(
                code=fixed_location_code,
                crosswalk=cls.country_code_crosswalk,
                record_id=cls.get_source_record_id(source_record),
                code_type="country",
            )
        ):
            return timdex.Location(value=location_name, kind="Place of Publication")
        return None

    @classmethod
    def get_notes(cls, source_record: Tag) -> list[timdex.Note] | None:
        notes = []
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
            notes.extend(
                [
                    timdex.Note(
                        value=[note_value.rstrip(" .")],
                        kind=note_marc_field["kind"],
                    )
                    for datafield in source_record.find_all(
                        "datafield", tag=note_marc_field["tag"]
                    )
                    if (
                        note_value := (
                            cls.create_subfield_value_string_from_datafield(
                                datafield,
                                note_marc_field["subfields"],
                                " ",
                            )
                        )
                    )
                ]
            )
        return notes or None

    @classmethod
    def get_numbering(cls, source_record: Tag) -> str | None:
        return (
            cls.concatenate_subfield_value_strings_from_datafield(
                source_record, tag="362", subfield_codes="abcefg"
            )
            or None
        )

    @classmethod
    def get_physical_description(cls, source_record: Tag) -> str | None:
        return (
            cls.concatenate_subfield_value_strings_from_datafield(
                source_record, tag="300", subfield_codes="abcefg"
            )
            or None
        )

    @classmethod
    def get_publication_frequency(cls, source_record: Tag) -> list[str] | None:
        return [
            publication_frequency_value
            for datafield in source_record.find_all("datafield", tag="310")
            if (
                publication_frequency_value := (
                    cls.create_subfield_value_string_from_datafield(datafield, "a", " ")
                )
            )
        ] or None

    @classmethod
    def get_publishers(cls, source_record: Tag) -> list[timdex.Publisher] | None:
        publishers = []
        for publisher_marc_tag in ["260", "264"]:
            for datafield in source_record.find_all("datafield", tag=publisher_marc_tag):
                if any(
                    [
                        publisher_name := cls.get_single_subfield_string(datafield, "b"),
                        publisher_date := cls.get_single_subfield_string(datafield, "c"),
                        publisher_location := cls.get_single_subfield_string(
                            datafield, "a"
                        ),
                    ]
                ):
                    publishers.append(  # noqa: PERF401
                        timdex.Publisher(
                            name=publisher_name.rstrip(".,") if publisher_name else None,
                            date=publisher_date.rstrip(".,") if publisher_date else None,
                            location=(
                                publisher_location.rstrip(" :")
                                if publisher_location
                                else None
                            ),
                        )
                    )
        return publishers or None

    @classmethod
    def get_related_items(cls, source_record: Tag) -> list[timdex.RelatedItem] | None:
        related_items = []
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
            related_items.extend(
                [
                    timdex.RelatedItem(
                        description=related_item_value.rstrip(" ."),
                        relationship=related_item_marc_field["relationship"],
                    )
                    for datafield in source_record.find_all(
                        "datafield", tag=related_item_marc_field["tag"]
                    )
                    if (
                        related_item_value := (
                            cls.create_subfield_value_string_from_datafield(
                                datafield,
                                related_item_marc_field["subfields"],
                                " ",
                            )
                        )
                    )
                ]
            )
        return related_items or None

    @classmethod
    def get_subjects(cls, source_record: Tag) -> list[timdex.Subject] | None:
        subjects = []
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
            subjects.extend(
                [
                    timdex.Subject(
                        value=[subject_value.rstrip(" .")],
                        kind=subject_marc_field["kind"],
                    )
                    for datafield in source_record.find_all(
                        "datafield", tag=subject_marc_field["tag"]
                    )
                    if (
                        subject_value := (
                            cls.create_subfield_value_string_from_datafield(
                                datafield,
                                subject_marc_field["subfields"],
                                " - ",
                            )
                        )
                    )
                ]
            )
        return subjects or None

    @classmethod
    def get_summary(cls, source_record: Tag) -> list[str] | None:
        return [
            summary_value
            for datafield in source_record.find_all("datafield", tag="520")
            if (
                summary_value := cls.create_subfield_value_string_from_datafield(
                    datafield, "a", " "
                )
            )
        ] or None

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
