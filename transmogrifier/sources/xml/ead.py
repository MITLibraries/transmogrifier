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

        source_record_id = self.get_source_record_id(source_record)

        # <archdesc> and <did> elements are required when deriving optional fields
        collection_description = self._get_collection_description(source_record)
        collection_description_did = self._get_collection_description_did(source_record)

        # <controlaccess> element is optional (used by multiple optional fields)
        control_access_elements = self._get_control_access(source_record)

        # alternate_titles
        fields["alternate_titles"] = self.get_alternate_titles(source_record)

        # call_numbers field not used in EAD

        # citation
        fields["citation"] = self.get_citation(source_record)

        # content_type
        fields["content_type"] = self.get_content_type(source_record)
        # contents
        for arrangement_element in collection_description.find_all(
            "arrangement", recursive=False
        ):
            for arrangement_value in self.create_list_from_mixed_value(
                arrangement_element, skipped_elements=["head"]
            ):
                fields.setdefault("contents", []).append(arrangement_value)

        # contributors
        for origination_element in collection_description_did.find_all("origination"):
            for name_element in origination_element.find_all(name=True, recursive=False):
                if name_value := self.create_string_from_mixed_value(
                    name_element, separator=" "
                ):
                    fields.setdefault("contributors", []).append(
                        timdex.Contributor(
                            value=name_value,
                            kind=origination_element.get("label") or None,
                            identifier=self.generate_name_identifier_url(name_element),
                        )
                    )

        # dates
        dates = self.parse_dates(collection_description_did, source_record_id)
        if dates:
            fields.setdefault("dates", []).extend(dates)

        # edition field not used in EAD

        # file_formats field not used in EAD

        # format field not used in EAD

        # funding_information field not used in EAD. titlestmt > sponsor was considered
        # but did not fit the usage of this field in other sources.

        # holdings omitted pending discussion on how to map originalsloc and physloc

        # identifiers
        for id_element in collection_description_did.find_all("unitid", recursive=False):
            if id_element.get("type") == "aspace_uri":
                continue
            if id_value := self.create_string_from_mixed_value(
                id_element,
                separator=" ",
            ):
                fields.setdefault("identifiers", []).append(
                    timdex.Identifier(value=id_value, kind="Collection Identifier")
                )

        # languages
        for langmaterial_element in collection_description_did.find_all(
            "langmaterial", recursive=False
        ):
            for language_element in langmaterial_element.find_all("language"):
                if language_value := self.create_string_from_mixed_value(
                    language_element
                ):
                    fields.setdefault("languages", []).append(language_value)

        # links, omitted pending decision on duplicating source_link

        # literary_form field not used in EAD

        # locations
        for control_access_element in control_access_elements:
            for location_element in control_access_element.find_all("geogname"):
                if location_value := self.create_string_from_mixed_value(
                    location_element,
                    separator=" ",
                ):
                    fields.setdefault("locations", []).append(
                        timdex.Location(value=location_value)
                    )

        # notes
        for note_element in collection_description.find_all(
            [
                "bibliography",
                "bioghist",
                "scopecontent",
            ],
            recursive=False,
        ):
            subelement_tag = "bibref" if note_element.name == "bibliography" else "p"
            note_value = []
            for subelement in note_element.find_all(subelement_tag, recursive=False):
                if subelement_value := self.create_string_from_mixed_value(
                    subelement,
                    separator=" ",
                ):
                    note_value.append(subelement_value)  # noqa: PERF401
            if note_value:
                note_head_element = note_element.find("head", string=True)
                fields.setdefault("notes", []).append(
                    timdex.Note(
                        value=note_value,
                        kind=(
                            note_head_element.string
                            if note_head_element
                            else aspace_type_crosswalk.get(
                                note_element.name, note_element.name
                            )
                        ),
                    )
                )

        # numbering field not used in EAD

        # physical_description
        physical_descriptions = []
        for physical_description_element in collection_description_did.find_all(
            "physdesc", recursive=False
        ):
            if physical_description_value := self.create_string_from_mixed_value(
                physical_description_element, separator=" "
            ):
                physical_descriptions.append(physical_description_value)  # noqa: PERF401
        if physical_descriptions:
            fields["physical_description"] = "; ".join(physical_descriptions)

        # publication_frequency field not used in EAD

        # publishers
        if publication_element := collection_description_did.find(  # noqa: SIM102
            "repository"
        ):
            if publication_value := self.create_string_from_mixed_value(
                publication_element, separator=" "
            ):
                fields["publishers"] = [timdex.Publisher(name=publication_value)]

        # related_items
        for related_item_element in collection_description.find_all(
            ["altformavail", "separatedmaterial"],
            recursive=False,
        ):
            if related_item_value := self.create_string_from_mixed_value(
                related_item_element, separator=" ", skipped_elements=["head"]
            ):
                fields.setdefault("related_items", []).append(
                    timdex.RelatedItem(
                        description=related_item_value,
                        relationship=aspace_type_crosswalk.get(
                            related_item_element.name, related_item_element.name
                        ),
                    )
                )
        for related_item_element in collection_description.find_all(
            ["relatedmaterial"],
            recursive=False,
        ):
            if list_element := related_item_element.find("list"):
                subelements = list_element.find_all("defitem")
            else:
                subelements = related_item_element.find_all("p", recursive=False)
            for subelement in subelements:
                if related_item_value := self.create_string_from_mixed_value(
                    subelement, separator=" ", skipped_elements=["head"]
                ):
                    fields.setdefault("related_items", []).append(
                        timdex.RelatedItem(
                            description=related_item_value,
                        )
                    )

        # rights
        for rights_element in collection_description.find_all(
            ["accessrestrict", "userestrict"], recursive=False
        ):
            if rights_value := self.create_string_from_mixed_value(
                rights_element, separator=" ", skipped_elements=["head"]
            ):
                fields.setdefault("rights", []).append(
                    timdex.Rights(
                        description=rights_value,
                        kind=aspace_type_crosswalk.get(
                            rights_element.name, rights_element.name
                        ),
                    )
                )

        # subjects
        for control_access_element in control_access_elements:
            for subject_element in control_access_element.find_all(
                name=True, recursive=False
            ):
                if subject_value := self.create_string_from_mixed_value(
                    subject_element, separator=" "
                ):
                    subject_source = subject_element.get("source")
                    fields.setdefault("subjects", []).append(
                        timdex.Subject(
                            value=[subject_value],
                            kind=aspace_type_crosswalk.get(subject_source, subject_source)
                            or None,
                        ),
                    )

        # summary
        abstract_values = []
        for abstract_element in collection_description_did.find_all(
            "abstract", recursive=False
        ):
            if abstract_value := self.create_string_from_mixed_value(
                abstract_element, separator=" "
            ):
                abstract_values.append(abstract_value)  # noqa: PERF401
        fields["summary"] = abstract_values or None

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
    def generate_name_identifier_url(cls, name_element: Tag) -> list | None:
        """
        Generate a full name identifier URL with the specified scheme.

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
        control_access_elements = cls._get_control_access(source_record)
        for control_access_element in control_access_elements:
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

    def parse_dates(
        self, collection_description_did: Tag, source_record_id: str
    ) -> list[timdex.Date]:
        """
        Dedicated method to parse dates.  Targeting archdesc.unitdata elements, using
        only those with a @normal attribute value.  These are almost uniformly ranges,
        but in the event they are not (or two identical values for the range) a single
        date value is produced.
        """
        dates = []
        for date_element in collection_description_did.find_all("unitdate"):
            normal_date = date_element.get("normal", "").strip()
            if normal_date == "":
                continue

            date_instance = timdex.Date()

            # date range
            if "/" in normal_date:
                gte_date, lte_date = normal_date.split("/")
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
                    date_str = gte_date  # arbitrarily take one
                    if validate_date(
                        date_str,
                        source_record_id,
                    ):
                        date_instance.value = date_str

            # fallback on single date
            elif validate_date(normal_date, source_record_id):
                date_instance.value = normal_date

            # include @datechar and @certainty attributes
            date_instance.kind = date_element.get("datechar")
            date_instance.note = date_element.get("certainty")

            if date_instance.range or date_instance.value:
                dates.append(date_instance)

        return dates
