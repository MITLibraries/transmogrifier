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

    @staticmethod
    def create_subfield_value_list_from_datafield(
        xml_element: Tag,
        subfield_codes: list | str,
    ) -> list:
        """
        Create a list of values from the specified subfields of a
        datafield element.

        Given an XML element with values from subfield code "a":

            <datafield tag="<tag>">
                <subfield code="a">value 1</subfield>
                <subfield code="a">value 2</subfield>
            </datafield>

        The method returns the output: [value 1, value2].

        Args:
            xml_element: A BeautifulSoup Tag representing a single MARC XML element.
            subfield_codes: Subfield codes from which values are extracted.
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
        Create a string by joining a list of subfield values from a
        datafield element.

        For example, given an XML element with values from subfield codes "ab"
        and using separator = " - ":

            <datafield tag="<tag>">
                <subfield code="a">value 1</subfield>
                <subfield code="b">value 2</subfield>
            </datafield>

        The method returns the output: "value 1 - value 2".

        Args:
            xml_element: A BeautifulSoup Tag representing a single MARC XML element.
            subfield_codes: Subfield codes from which values are extracted.
            separator: String value used for joining values.
        """
        return separator.join(
            Marc.create_subfield_value_list_from_datafield(xml_element, subfield_codes)
        )

    @classmethod
    def concatenate_subfield_value_strings_from_datafield(
        cls, source_record: Tag, tag: str, subfield_codes: str
    ) -> str:
        """
        Create a string by joining a list of subfield value strings
        from a datafield element.

        For example, given an XML element with values from subfield codes "ab"
        and using separator = " - ":

            <datafield tag="<tag">
                <subfield code="a">value 1</subfield>
                <subfield code="b">value 2</subfield>
            </datafield>
            <datafield tag="<tag>">
                <subfield code="a">value 3</subfield>
                <subfield code="a">value 4</subfield>
            </datafield>

        the method returns the output: "value 1 value 2 value 3 value 4".

        Args:
            source_record (Tag): A BeautifulSoup Tag representing a single
                MARC XML record.
            tag (str): Variable data field tag which is denoted in the "tag"
                attribute of a MARC 'datafield' XML element.
            subfield_codes (str): Subfield codes from which values are
                extracted.
        """
        return " ".join(
            cls.create_subfield_value_string_from_datafield(
                datafield, subfield_codes, " "
            )
            for datafield in source_record.find_all("datafield", tag=tag)
        )

    @staticmethod
    def get_single_subfield_string(xml_element: Tag, subfield_code: str) -> str | None:
        """
        Get the string value of a subfield element for a specified code.

        Finds and returns the string value of a single subfield element if the
        element contains a string. This uses bs4's find() method and thus will return
        only the string value from the first subfield element matching the criteria.

        Args:
            xml_element: A BeautifulSoup Tag representing a single MARC XML element.
            subfield_code: Subfield code from which a single value is extracted.

        Returns:
            str | None: If a matching subfield element containing a string is found
                and the value is not only whitespace, the string value is returned;
                else None is returned.
        """
        if subfield := xml_element.find("subfield", code=subfield_code, string=True):
            return str(subfield.string).strip() or None
        return None

    @staticmethod
    def json_crosswalk_code_to_name(
        code: str, crosswalk: dict, record_id: str, field_name: str
    ) -> str | None:
        """
        Retrieve the name associated with a given code from a JSON crosswalk.
        If the code is not found in the crosswalk, a DEBUG message is logged.

        Args:
            code: The code from a MARC record.
            crosswalk: The crosswalk dict to use, loaded from a config file.
            record_id: The MMS ID of the MARC record.
            field_name: The MARC field containing the code.

        Returns:
            str | None: If a mapping for the code is found in the crosswalk, the
                mapped value is returned; else None is returned.
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
        code crosswalk. If the code is obsolete or the code is not found in the crosswalk,
        a DEBUG message is logged.

        Args:
            code: The code from a MARC record.
            crosswalk: The crosswalked bs4 Tag to use, loaded from a config file.
            record_id: The MMS ID of the MARC record.
            code_type: The type of code, e.g. country or language.

        Returns:
            str | None: If a mapping for the code is found in the crosswalk, the
                mapped value is returned; else None is returned.
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
            ("130", "adfghklmnoprst", "Preferred Title"),
            ("240", "adfghklmnoprs", "Preferred Title"),
            ("246", "abfghinp", "Varying Form of Title"),
            ("730", "adfghiklmnoprst", "Preferred Title"),
            ("740", "anp", "Uncontrolled Related/Analytical Title"),
        ]
        for tag, subfield_codes, kind in alternate_title_marc_fields:
            alternate_titles.extend(
                [
                    timdex.AlternateTitle(
                        value=alternate_title_value.rstrip(" .,/"),
                        kind=kind,
                    )
                    for datafield in source_record.find_all("datafield", tag=tag)
                    if (
                        alternate_title_value := (
                            cls.create_subfield_value_string_from_datafield(
                                xml_element=datafield,
                                subfield_codes=subfield_codes,
                                separator=" ",
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
            ("100", "abcq"),
            ("110", "abc"),
            ("111", "acdfgjq"),
            ("700", "abcq"),
            ("710", "abc"),
            ("711", "acdfgjq"),
        ]

        for tag, subfields in contributor_marc_fields:
            for datafield in source_record.find_all("datafield", tag=tag):
                if contributor_name := (
                    cls.create_subfield_value_string_from_datafield(
                        xml_element=datafield,
                        subfield_codes=subfields,
                        separator=" ",
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
                    xml_element=datafield, subfield_codes="ab", separator=" "
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
            ("010", "a", "LCCN"),
            ("020", "aq", "ISBN"),
            ("022", "a", "ISSN"),
            ("024", "aq2", "Other Identifier"),
            ("035", "a", "OCLC Number"),
        ]
        for tag, subfields, kind in identifier_marc_fields:
            identifiers.extend(
                [
                    timdex.Identifier(
                        value=identifier.strip().replace("(OCoLC)", ""),
                        kind=kind,
                    )
                    for datafield in source_record.find_all("datafield", tag=tag)
                    if (
                        identifier := (
                            cls.create_subfield_value_string_from_datafield(
                                xml_element=datafield,
                                subfield_codes=subfields,
                                separator=". ",
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
                    code=language_code,
                    crosswalk=cls.language_code_crosswalk,
                    record_id=cls.get_source_record_id(source_record),
                    code_type="language",
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
            ("751", "a", "Geographic Name"),
            ("752", "abcdefgh", "Hierarchical Place Name"),
        ]
        # get locations (place of publication) from control field 008/15-17
        if place_of_publication := cls._get_location_publication(source_record):
            locations.append(place_of_publication)

        # get locations from data fields
        for tag, subfields, kind in location_marc_fields:
            locations.extend(
                [
                    timdex.Location(
                        value=location_value.rstrip(" .,/)"),
                        kind=kind,
                    )
                    for datafield in source_record.find_all("datafield", tag=tag)
                    if (
                        location_value := (
                            cls.create_subfield_value_string_from_datafield(
                                xml_element=datafield,
                                subfield_codes=subfields,
                                separator=" - ",
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
            ("245", "c", "Title Statement of Responsibility"),
            ("500", "a", "General Note"),
            ("502", "abcdg", "Dissertation Note"),
            ("504", "a", "Bibliography Note"),
            (
                "508",
                "a",
                "Creation/Production Credits Note",
            ),
            ("511", "a", "Participant or Performer Note"),
            ("515", "a", "Numbering Peculiarities Note"),
            ("522", "a", "Geographic Coverage Note"),
            ("533", "abcdefmn", "Reproduction Note"),
            ("534", "abcefklmnoptxz", "Original Version Note"),
            ("588", "a", "Source of Description Note"),
            ("590", "a", "Local Note"),
        ]
        for tag, subfields, kind in note_marc_fields:
            notes.extend(
                [
                    timdex.Note(
                        value=[note_value.rstrip(" .")],
                        kind=kind,
                    )
                    for datafield in source_record.find_all("datafield", tag=tag)
                    if (
                        note_value := (
                            cls.create_subfield_value_string_from_datafield(
                                xml_element=datafield,
                                subfield_codes=subfields,
                                separator=" ",
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
                    cls.create_subfield_value_string_from_datafield(
                        xml_element=datafield, subfield_codes="a", separator=" "
                    )
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
            ("765", "abcdghikmnorstuwxyz", "Original Language Version"),
            ("770", "abcdghikmnorstuwxyz", "Has Supplement"),
            ("772", "abcdghikmnorstuwxyz", "Supplement To"),
            ("780", "abcdghikmnorstuwxyz", "Previous Title"),
            ("785", "abcdghikmnorstuwxyz", "Subsequent Title"),
            ("787", "abcdghikmnorstuwxyz", "Not Specified"),
            ("830", "adfghklmnoprstvwx", "In Series"),
            ("510", "abcx", "In Bibliography"),
        ]
        for tag, subfields, relationship in related_item_marc_fields:
            related_items.extend(
                [
                    timdex.RelatedItem(
                        description=related_item_value.rstrip(" ."),
                        relationship=relationship,
                    )
                    for datafield in source_record.find_all("datafield", tag=tag)
                    if (
                        related_item_value := (
                            cls.create_subfield_value_string_from_datafield(
                                xml_element=datafield,
                                subfield_codes=subfields,
                                separator=" ",
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
            ("600", "abcdefghjklmnopqrstuvxyz", "Personal Name"),
            ("610", "abcdefghklmnoprstuvxyz", "Corporate Name"),
            ("650", "avxyz", "Topical Term"),
            ("651", "avxyz", "Geographic Name"),
        ]
        for tag, subfields, kind in subject_marc_fields:
            subjects.extend(
                [
                    timdex.Subject(
                        value=[subject_value.rstrip(" .")],
                        kind=kind,
                    )
                    for datafield in source_record.find_all("datafield", tag=tag)
                    if (
                        subject_value := (
                            cls.create_subfield_value_string_from_datafield(
                                xml_element=datafield,
                                subfield_codes=subfields,
                                separator=" - ",
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
                    xml_element=datafield, subfield_codes="a", separator=" "
                )
            )
        ] or None

    @classmethod
    def get_main_titles(cls, source_record: Tag) -> list[str]:
        """
        Retrieve main title(s) from a MARC XML record.

        Overrides metaclass get_main_titles() method.

        Args:
            source_record: A BeautifulSoup Tag representing a single MARC XML record.
        """
        try:
            main_title_values = []
            if main_title_value := cls.create_subfield_value_string_from_datafield(
                xml_element=source_record.find("datafield", tag="245"),
                subfield_codes="abfgknps",
                separator=" ",
            ):
                main_title_values.append(main_title_value.rstrip(" .,/"))
        except AttributeError:
            logger.exception(
                "Record ID %s is missing a 245 field",
                cls.get_source_record_id(source_record),
            )
            return []
        else:
            return main_title_values

    @classmethod
    def get_source_record_id(cls, source_record: Tag) -> str:
        """
        Get the source record ID from a MARC XML record.

        Overrides metaclass get_source_record_id() method.

        Args:
            source_record: A BeautifulSoup Tag representing a single MARC XML record.
        """
        return str(source_record.find("controlfield", tag="001", string=True).string)

    @classmethod
    def record_is_deleted(cls, source_record: Tag) -> bool:
        """
        Determine whether record has a status of deleted.

        Overrides metaclass record_is_deleted() method.

        Args:
            source_record: A BeautifulSoup Tag representing a single MARC XML record
        """
        if leader := source_record.find("leader", string=True):  # noqa: SIM102
            if leader.string[5:6] == "d":
                return True
        return False
