import logging
from collections.abc import Generator

from bs4 import NavigableString, Tag  # type: ignore[import-untyped]

import transmogrifier.models as timdex
from transmogrifier.config import load_external_config
from transmogrifier.exceptions import SkippedRecordEvent
from transmogrifier.helpers import validate_date, validate_date_range
from transmogrifier.sources.xmltransformer import XMLTransformer

logger = logging.getLogger(__name__)


aspace_type_crosswalk = load_external_config("config/aspace_type_crosswalk.json", "json")


class Ead(XMLTransformer):
    """EAD transformer."""

    def get_optional_fields(self, source_record: Tag) -> dict | None:
        """
        Retrieve optional TIMDEX fields from an EAD XML record.

        Overrides metaclass get_optional_fields() method.

        Args:
            source_record: A BeautifulSoup Tag representing a single EAD XML record.
        """
        fields: dict = {}

        # alternate_titles
        fields["alternate_titles"] = self.get_alternate_titles(source_record)

        # call_numbers field not used in EAD

        # citation
        fields["citation"] = self.get_citation(source_record)

        # content_type
        fields["content_type"] = self.get_content_type(source_record)

        # contents
        fields["contents"] = self.get_contents(source_record)

        # contributors
        fields["contributors"] = self.get_contributors(source_record)

        # dates
        fields["dates"] = self.get_dates(source_record)

        # edition field not used in EAD

        # file_formats field not used in EAD

        # format field not used in EAD

        # funding_information field not used in EAD. titlestmt > sponsor was considered
        # but did not fit the usage of this field in other sources.

        # holdings omitted pending discussion on how to map originalsloc and physloc

        # identifiers
        fields["identifiers"] = self.get_identifiers(source_record)

        # languages
        fields["languages"] = self.get_languages(source_record)

        # links, omitted pending decision on duplicating source_link

        # literary_form field not used in EAD

        # locations
        fields["locations"] = self.get_locations(source_record)

        # notes
        fields["notes"] = self.get_notes(source_record)

        # numbering field not used in EAD

        # physical_description
        fields["physical_description"] = self.get_physical_description(source_record)

        # publication_frequency field not used in EAD

        # publishers
        fields["publishers"] = self.get_publishers(source_record)

        # related_items
        fields["related_items"] = self.get_related_items(source_record)

        # rights
        fields["rights"] = self.get_rights(source_record)

        # subjects
        fields["subjects"] = self.get_subjects(source_record)

        # summary
        fields["summary"] = self.get_summary(source_record)

        return fields

    @classmethod
    def create_list_from_mixed_value(
        cls, xml_element: Tag, skipped_elements: list[str] | None = None
    ) -> list:
        """
        Create a list of strings from an XML element value that contains a mix of strings
        and XML elements.

        Args:
            xml_element: An XML element that may contain a value consisting of
            strings and XML elements.
            skipped_elements: Elements that should be skipped when parsing the mixed
            value.
        """
        if skipped_elements is None:
            skipped_elements = []
        value_list = []
        for contents_child in xml_element.children:
            for value in cls.parse_mixed_value(contents_child, skipped_elements):
                if value not in value_list:
                    value_list.append(value)
        return value_list

    @classmethod
    def create_string_from_mixed_value(
        cls,
        xml_element: Tag,
        separator: str = "",
        skipped_elements: list[str] | None = None,
    ) -> str:
        """
        Create a joined string from a list of strings from an XML element value
        that contains a mix of strings and XML elements.

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
    def _get_collection_description(cls, source_record: Tag) -> Tag:
        """Get element with archival description for a collection.

        For EAD-formatted XML, all of the information about a collection
        that is relevant to the TIMDEX data model is
        encapsulated within the <archdesc level="collection"> element.
        If this element is missing, it suggests that there is a structural
        error in the record.

        This method is used by multiple field methods.
        """
        if collection_description := source_record.metadata.find(
            "archdesc", level="collection"
        ):
            return collection_description
        message = (
            "Record skipped because key information is missing: "
            '<archdesc level="collection">.'
        )
        raise SkippedRecordEvent(message)

    @classmethod
    def _get_collection_description_did(cls, source_record: Tag) -> Tag:
        """Get element with descriptive identification for a collection.

        For EAD-formatted XML, information essential
        for identifying the material being described is encapsulated within
        the <did> element (nested within the <archdesc> element).
        If this element is missing, the required TIMDEX field 'title'
        cannot be derived.

        This method is used by multiple field methods.
        """
        collection_description = cls._get_collection_description(source_record)
        if collection_description_did := collection_description.did:
            return collection_description_did
        message = "Record skipped because key information is missing: <did>."
        raise SkippedRecordEvent(message)

    @classmethod
    def _get_control_access(cls, source_record: Tag) -> list[Tag]:
        """Get elements with control access headings for a collection.

        For EAD-formatted XML, information essential
        for identifying the material being described is encapsulated within
        the <did> element (nested within the <archdesc> element).
        If this element is missing, the required TIMDEX field 'title'
        cannot be derived.

        This method is used by multiple field methods.
        """
        collection_description = cls._get_collection_description(source_record)
        return collection_description.find_all("controlaccess", recursive=False)

    @classmethod
    def get_alternate_titles(
        cls, source_record: Tag
    ) -> list[timdex.AlternateTitle] | None:
        """Retrieve extra titles from get_main_titles."""
        return [
            timdex.AlternateTitle(value=title)
            for index, title in enumerate(cls.get_main_titles(source_record))
            if index > 0 and title
        ] or None

    @classmethod
    def get_citation(cls, source_record: Tag) -> str | None:
        collection_description = cls._get_collection_description(source_record)
        if (
            citation_element := collection_description.find("prefercite", recursive=False)
        ) and (
            citation := cls.create_string_from_mixed_value(
                citation_element, separator=" ", skipped_elements=["head"]
            )
        ):
            return citation
        return None

    @classmethod
    def get_content_type(cls, source_record: Tag) -> list[str] | None:
        content_types = ["Archival materials"]
        for control_access_element in cls._get_control_access(source_record):
            _content_types = [
                content_type
                for content_type_element in control_access_element.find_all("genreform")
                if (
                    content_type := cls.create_string_from_mixed_value(
                        content_type_element, separator=" "
                    )
                )
            ]
            content_types.extend(_content_types)

        return content_types or None

    @classmethod
    def get_contents(cls, source_record: Tag) -> list[str] | None:
        contents = []
        collection_description = cls._get_collection_description(source_record)
        for arrangement_element in collection_description.find_all(
            "arrangement", recursive=False
        ):
            contents.extend(
                cls.create_list_from_mixed_value(
                    arrangement_element, skipped_elements=["head"]
                )
            )
        return contents or None

    @classmethod
    def get_contributors(cls, source_record: Tag) -> list[timdex.Contributor] | None:
        contributors = []
        collection_description_did = cls._get_collection_description_did(source_record)
        for origination_element in collection_description_did.find_all("origination"):
            contributors.extend(
                [
                    timdex.Contributor(
                        value=contributor_name,
                        kind=origination_element.get("label") or None,
                        identifier=cls._get_contributor_identifier_url(
                            contributor_element
                        ),
                    )
                    for contributor_element in origination_element.find_all(
                        name=True, recursive=False
                    )
                    if (
                        contributor_name := cls.create_string_from_mixed_value(
                            contributor_element, separator=" "
                        )
                    )
                ]
            )

        return contributors or None

    @classmethod
    def _get_contributor_identifier_url(cls, name_element: Tag) -> list | None:
        """Generate a full name identifier URL with the specified scheme.

        Args:
            name_element: A BeautifulSoup Tag representing an EAD
                name XML field.
        """
        if identifier := name_element.get("authfilenumber"):
            source = name_element.get("source")
            if source in ["lcnaf", "naf"]:
                base_url = "https://lccn.loc.gov/"
            elif source == "snac":
                base_url = "https://snaccooperative.org/view/"
            elif source == "viaf":
                base_url = "http://viaf.org/viaf/"
            else:
                base_url = ""
            return [base_url + identifier]
        return None

    @classmethod
    def get_dates(cls, source_record: Tag) -> list[timdex.Date] | None:
        dates = []
        source_record_id = cls.get_source_record_id(source_record)
        dates.extend(
            cls._parse_date_elements(
                cls._get_collection_description_did(source_record), source_record_id
            )
        )
        return dates or None

    @classmethod
    def _parse_date_elements(
        cls, collection_description_did: Tag, source_record_id: str
    ) -> list[timdex.Date]:
        """
        Dates are derived from <archdesc><unitdate> elements with the @normal attribute.

        The method will iterate over these elements, validating the values assigned to
        the @normal attribute. If the date value passes validation, a timdex.Date
        instance is created and added to the list of valid timdex.Dates that is
        returned.

        Note: If the date values in a provided date range are the same, a
          single date is retrieved.
        """
        dates = []
        for date_element in collection_description_did.find_all("unitdate", normal=True):
            date_string = date_element.get("normal", "").strip()

            if date_string == "":
                continue

            date_instance = timdex.Date()

            # get valid date ranges or dates
            if "/" in date_string:
                date_instance = cls._parse_date_range(date_string, source_record_id)
            elif validate_date(date_string, source_record_id):
                date_instance.value = date_string

            # include @datechar and @certainty attributes
            date_instance.kind = date_element.get("datechar")
            date_instance.note = date_element.get("certainty")

            if date_instance.range or date_instance.value:
                dates.append(date_instance)
        return dates

    @classmethod
    def _parse_date_range(cls, date_string: str, source_record_id: str) -> timdex.Date:
        date_instance = timdex.Date()
        gte_date, lte_date = date_string.split("/")
        if gte_date != lte_date:
            if validate_date_range(
                gte_date,
                lte_date,
                source_record_id,
            ):
                date_instance.range = timdex.DateRange(
                    gte=gte_date,
                    lte=lte_date,
                )
        else:
            # get valid date (if dates in ranges are the same)
            date_string = gte_date
            if validate_date(
                date_string,
                source_record_id,
            ):
                date_instance.value = date_string
        return date_instance

    @classmethod
    def get_identifiers(cls, source_record: Tag) -> list[timdex.Identifier] | None:
        identifiers = []
        collection_description_did = cls._get_collection_description_did(source_record)
        for id_element in collection_description_did.find_all("unitid", recursive=False):
            if id_element.get("type") == "aspace_uri":
                continue
            if id_value := cls.create_string_from_mixed_value(
                id_element,
                separator=" ",
            ):
                identifiers.append(
                    timdex.Identifier(value=id_value, kind="Collection Identifier")
                )
        return identifiers or None

    @classmethod
    def get_languages(cls, source_record: Tag) -> list[str] | None:
        languages = []
        collection_description_did = cls._get_collection_description_did(source_record)
        for langmaterial_element in collection_description_did.find_all(
            "langmaterial", recursive=False
        ):
            languages.extend(
                [
                    language
                    for language_element in langmaterial_element.find_all("language")
                    if (language := cls.create_string_from_mixed_value(language_element))
                ]
            )
        return languages or None

    @classmethod
    def get_locations(cls, source_record: Tag) -> list[timdex.Location] | None:
        locations = []
        for control_access_element in cls._get_control_access(source_record):
            locations.extend(
                [
                    timdex.Location(value=location)
                    for location_element in control_access_element.find_all("geogname")
                    if (
                        location := cls.create_string_from_mixed_value(
                            location_element,
                            separator=" ",
                        )
                    )
                ]
            )

        return locations or None

    @classmethod
    def get_notes(cls, source_record: Tag) -> list[timdex.Note] | None:
        notes = []
        collection_description = cls._get_collection_description(source_record)
        for note_element in collection_description.find_all(
            [
                "bibliography",
                "bioghist",
                "scopecontent",
            ],
            recursive=False,
        ):
            subelement_tag = "bibref" if note_element.name == "bibliography" else "p"
            _notes = [
                note
                for subelement in note_element.find_all(subelement_tag, recursive=False)
                if (
                    note := cls.create_string_from_mixed_value(
                        subelement,
                        separator=" ",
                    )
                )
            ]

            if _notes:
                notes.append(
                    timdex.Note(
                        value=_notes,
                        kind=cls._get_note_kind(note_element),
                    )
                )
        return notes or None

    @classmethod
    def _get_note_kind(cls, note_element: Tag) -> str:
        if head_element := note_element.find("head", string=True):
            return str(head_element.string)
        return aspace_type_crosswalk.get(note_element.name, note_element.name)

    @classmethod
    def get_physical_description(cls, source_record: Tag) -> str | None:
        collection_description_did = cls._get_collection_description_did(source_record)
        physical_descriptions = [
            physical_description
            for physical_description_element in collection_description_did.find_all(
                "physdesc", recursive=False
            )
            if (
                physical_description := cls.create_string_from_mixed_value(
                    physical_description_element, separator=" "
                )
            )
        ]
        return "; ".join(physical_descriptions) or None

    @classmethod
    def get_publishers(cls, source_record: Tag) -> list[timdex.Publisher] | None:
        collection_description_did = cls._get_collection_description_did(source_record)
        if (publication_element := collection_description_did.find("repository")) and (
            publication_value := cls.create_string_from_mixed_value(
                publication_element, separator=" "
            )
        ):
            return [timdex.Publisher(name=publication_value)]
        return None

    @classmethod
    def get_related_items(cls, source_record: Tag) -> list[timdex.RelatedItem] | None:
        related_items = []
        collection_description = cls._get_collection_description(source_record)

        for related_item_element in collection_description.find_all(
            ["altformavail", "relatedmaterial", "separatedmaterial"], recursive=False
        ):
            if related_item_element.name == "relatedmaterial":
                related_items.extend(
                    cls._get_related_item_from_relatedmaterial(related_item_element)
                )
            elif related_item := cls.create_string_from_mixed_value(
                related_item_element, separator=" ", skipped_elements=["head"]
            ):
                related_items.append(
                    timdex.RelatedItem(
                        description=related_item,
                        relationship=aspace_type_crosswalk.get(
                            related_item_element.name, related_item_element.name
                        ),
                    )
                )
        return related_items or None

    @classmethod
    def _get_related_item_from_relatedmaterial(
        cls, related_material_element: Tag
    ) -> list[timdex.RelatedItem]:
        if list_element := related_material_element.find("list"):
            subelements = list_element.find_all("defitem")
        else:
            subelements = related_material_element.find_all("p", recursive=False)

        return [
            timdex.RelatedItem(description=related_item)
            for subelement in subelements
            if (
                related_item := cls.create_string_from_mixed_value(
                    subelement, separator=" ", skipped_elements=["head"]
                )
            )
        ]

    @classmethod
    def get_rights(cls, source_record: Tag) -> list[timdex.Rights] | None:
        collection_description = cls._get_collection_description(source_record)
        return [
            timdex.Rights(
                description=rights,
                kind=aspace_type_crosswalk.get(rights_element.name, rights_element.name),
            )
            for rights_element in collection_description.find_all(
                ["accessrestrict", "userestrict"], recursive=False
            )
            if (
                rights := cls.create_string_from_mixed_value(
                    rights_element, separator=" ", skipped_elements=["head"]
                )
            )
        ] or None

    @classmethod
    def get_subjects(cls, source_record: Tag) -> list[timdex.Subject] | None:
        subjects = []
        for control_access_element in cls._get_control_access(source_record):
            subjects.extend(
                [
                    timdex.Subject(
                        value=[subject_value],
                        kind=aspace_type_crosswalk.get(
                            subject_element.get("source"), subject_element.get("source")
                        )
                        or None,
                    )
                    for subject_element in control_access_element.find_all(
                        name=True, recursive=False
                    )
                    if (
                        subject_value := cls.create_string_from_mixed_value(
                            subject_element, separator=" "
                        )
                    )
                ]
            )
        return subjects or None

    @classmethod
    def get_summary(cls, source_record: Tag) -> list[str] | None:
        collection_description_did = cls._get_collection_description_did(source_record)
        return [
            abstract
            for abstract_element in collection_description_did.find_all(
                "abstract", recursive=False
            )
            if (
                abstract := cls.create_string_from_mixed_value(
                    abstract_element, separator=" "
                )
            )
        ] or None

    @classmethod
    def get_main_titles(cls, source_record: Tag) -> list[str]:
        """
        Retrieve main title(s) from an EAD XML record.

        Overrides metaclass get_main_titles() method.

        Args:
            source_record: A BeautifulSoup Tag representing a single EAD XML record.
        """
        try:
            unit_titles = source_record.metadata.find(
                "archdesc", level="collection"
            ).did.find_all("unittitle")
        except AttributeError:
            return []
        return [
            title
            for unit_title in unit_titles
            if (
                title := cls.create_string_from_mixed_value(
                    unit_title, separator=" ", skipped_elements=["num"]
                )
            )
        ]

    @classmethod
    def get_source_record_id(cls, source_record: Tag) -> str:
        """
        Get the source record ID from an EAD XML record.

        Overrides metaclass get_source_record_id() method.

        Args:
            source_record: A BeautifulSoup Tag representing a single EAD XML record.
        """
        return source_record.header.identifier.string.split("//")[1]

    @classmethod
    def parse_mixed_value(
        cls,
        item: NavigableString | Tag,
        skipped_elements: list[str] | None = None,
    ) -> Generator:
        """
        Parse an item in a mixed value of XML elements and strings according to its type.
        Recursive given the unpredictable structure of EAD values.

        Args:
            item: An item in a mixed value that may be a BeautifulSoup NavigableString or
            Tag.
            skipped_elements: Elements that should be skipped when parsing the mixed
            value.
        """
        if skipped_elements is None:
            skipped_elements = []
        if isinstance(item, NavigableString) and item.strip():
            yield str(item.strip())
        elif isinstance(item, Tag) and item.name not in skipped_elements:
            for child in item.children:
                yield from cls.parse_mixed_value(child, skipped_elements)
