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
            source_record (Tag): A BeautifulSoup Tag representing a single EAD XML record.
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
        collection_description = cls._get_collection_description(source_record)
        if collection_description_did := collection_description.did:
            return collection_description_did
        message = "Record skipped because key information is missing: <did>."
        raise SkippedRecordEvent(message)

    @classmethod
    def _get_control_access(cls, source_record: Tag) -> Tag:
        collection_description = cls._get_collection_description(source_record)
        if control_access := collection_description.find_all(
            "controlaccess", recursive=False
        ):
            return control_access
        return None

    @classmethod
    def get_alternate_titles(
        cls, source_record: Tag
    ) -> list[timdex.AlternateTitle] | None:
        return [
            timdex.AlternateTitle(value=title)
            for index, title in enumerate(cls.get_main_titles(source_record))
            if index > 0 and title
        ] or None

    @classmethod
    def get_citation(cls, source_record: Tag) -> str | None:
        collection_description = cls._get_collection_description(source_record)
        if citation_element := collection_description.find(  # noqa: SIM102
            "prefercite", recursive=False
        ):
            if citation := cls.create_string_from_mixed_value(
                citation_element, " ", ["head"]
            ):
                return citation
        return None

    @classmethod
    def get_content_type(cls, source_record: Tag) -> list[str] | None:
        content_type = ["Archival materials"]
        if control_access := cls._get_control_access(source_record):
            for control_access_element in control_access:
                content_types = [
                    content_type_value
                    for content_type_element in control_access_element.find_all(
                        "genreform"
                    )
                    if (
                        content_type_value := cls.create_string_from_mixed_value(
                            content_type_element,
                            " ",
                        )
                    )
                ]
                content_type.extend(content_types)
        return content_type or None

    @classmethod
    def get_contents(cls, source_record: Tag) -> list[str] | None:
        contents = []
        collection_description = cls._get_collection_description(source_record)
        for arrangement_element in collection_description.find_all(
            "arrangement", recursive=False
        ):
            for arrangement_value in cls.create_list_from_mixed_value(
                arrangement_element, ["head"]
            ):
                contents.append(arrangement_value)  # noqa: PERF402
        return contents or None

    @classmethod
    def get_contributors(cls, source_record: Tag) -> list[timdex.Contributor] | None:
        contributors = []
        collection_description_did = cls._get_collection_description_did(source_record)
        for origination_element in collection_description_did.find_all("origination"):
            contributors.extend(
                [
                    timdex.Contributor(
                        value=name_value,
                        kind=origination_element.get("label") or None,
                        identifier=cls.generate_name_identifier_url(name_element),
                    )
                    for name_element in origination_element.find_all(
                        name=True, recursive=False
                    )
                    if (
                        name_value := cls.create_string_from_mixed_value(
                            name_element, " "
                        )
                    )
                ]
            )
        return contributors or None

    @classmethod
    def get_dates(cls, source_record: Tag) -> list[timdex.Date] | None:
        collection_description_did = cls._get_collection_description_did(source_record)
        source_record_id = cls.get_source_record_id(source_record)
        if dates := cls.parse_dates(collection_description_did, source_record_id):
            return dates
        return None

    @classmethod
    def get_identifiers(cls, source_record: Tag) -> list[timdex.Identifier] | None:
        identifiers = []
        collection_description = cls._get_collection_description_did(source_record)
        for id_element in collection_description.find_all("unitid", recursive=False):
            if id_element.get("type") == "aspace_uri":
                continue
            if id_value := cls.create_string_from_mixed_value(
                id_element,
                " ",
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
                    language_value
                    for language_element in langmaterial_element.find_all("language")
                    if (
                        language_value := cls.create_string_from_mixed_value(
                            language_element
                        )
                    )
                ]
            )
        return languages or None

    @classmethod
    def get_locations(cls, source_record: Tag) -> list[timdex.Location] | None:
        locations = []
        if control_access := cls._get_control_access(source_record):
            for control_access_element in control_access:
                locations.extend(
                    [
                        timdex.Location(value=location_value)
                        for location_element in control_access_element.find_all(
                            "geogname"
                        )
                        if (
                            location_value := cls.create_string_from_mixed_value(
                                location_element,
                                " ",
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
            note_value = []
            for subelement in note_element.find_all(subelement_tag, recursive=False):
                if subelement_value := cls.create_string_from_mixed_value(
                    subelement,
                    " ",
                ):
                    note_value.append(subelement_value)  # noqa: PERF401
            if note_value:
                note_head_element = note_element.find("head", string=True)
                notes.append(
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
        return notes or None

    @classmethod
    def get_physical_description(cls, source_record: Tag) -> str | None:
        collection_description_did = cls._get_collection_description_did(source_record)
        physical_descriptions = [
            physical_description_value
            for physical_description_element in collection_description_did.find_all(
                "physdesc", recursive=False
            )
            if (
                physical_description_value := cls.create_string_from_mixed_value(
                    physical_description_element, " "
                )
            )
        ]
        if physical_descriptions:
            return "; ".join(physical_descriptions)
        return None

    @classmethod
    def get_publishers(cls, source_record: Tag) -> list[timdex.Publisher] | None:
        collection_description_did = cls._get_collection_description_did(source_record)
        if publication_element := collection_description_did.find(  # noqa: SIM102
            "repository"
        ):
            if publication_value := cls.create_string_from_mixed_value(
                publication_element, " "
            ):
                return [timdex.Publisher(name=publication_value)]
        return None

    @classmethod
    def get_related_items(cls, source_record: Tag) -> list[timdex.RelatedItem] | None:
        related_items = []
        collection_description = cls._get_collection_description(source_record)

        related_items.extend(
            [
                timdex.RelatedItem(
                    description=related_item_value,
                    relationship=aspace_type_crosswalk.get(
                        related_item_element.name, related_item_element.name
                    ),
                )
                for related_item_element in collection_description.find_all(
                    ["altformavail", "separatedmaterial"],
                    recursive=False,
                )
                if (
                    related_item_value := cls.create_string_from_mixed_value(
                        related_item_element, " ", ["head"]
                    )
                )
            ]
        )

        for related_item_element in collection_description.find_all(
            ["relatedmaterial"],
            recursive=False,
        ):
            if list_element := related_item_element.find("list"):
                subelements = list_element.find_all("defitem")
            else:
                subelements = related_item_element.find_all("p", recursive=False)

            related_material = [
                timdex.RelatedItem(
                    description=related_item_value,
                )
                for subelement in subelements
                if (
                    related_item_value := cls.create_string_from_mixed_value(
                        subelement, " ", ["head"]
                    )
                )
            ]
            related_items.extend(related_material)
        return related_items or None

    @classmethod
    def get_rights(cls, source_record: Tag) -> list[timdex.Rights] | None:
        collection_description = cls._get_collection_description(source_record)
        return [
            timdex.Rights(
                description=rights_value,
                kind=aspace_type_crosswalk.get(rights_element.name, rights_element.name),
            )
            for rights_element in collection_description.find_all(
                ["accessrestrict", "userestrict"], recursive=False
            )
            if (
                rights_value := cls.create_string_from_mixed_value(
                    rights_element, " ", ["head"]
                )
            )
        ] or None

    @classmethod
    def get_subjects(cls, source_record: Tag) -> list[timdex.Subject] | None:
        subjects = []
        if control_access := cls._get_control_access(source_record):
            for control_access_element in control_access:
                for subject_element in control_access_element.find_all(
                    name=True, recursive=False
                ):
                    if subject_value := cls.create_string_from_mixed_value(
                        subject_element, " "
                    ):
                        subject_source = subject_element.get("source")
                        subjects.append(
                            timdex.Subject(
                                value=[subject_value],
                                kind=aspace_type_crosswalk.get(
                                    subject_source, subject_source
                                )
                                or None,
                            ),
                        )
        return subjects or None

    @classmethod
    def get_summary(cls, source_record: Tag) -> list[str] | None:
        collection_description_did = cls._get_collection_description_did(source_record)
        return [
            abstract_value
            for abstract_element in collection_description_did.find_all(
                "abstract", recursive=False
            )
            if (
                abstract_value := cls.create_string_from_mixed_value(
                    abstract_element, " "
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
        collection_description_did = cls._get_collection_description_did(source_record)
        unit_titles = collection_description_did.find_all("unittitle")
        return [
            title
            for unit_title in unit_titles
            if (title := cls.create_string_from_mixed_value(unit_title, " ", ["num"]))
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

    @classmethod
    def parse_dates(
        cls, collection_description_did: Tag, source_record_id: str
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
