import logging
from typing import Generator, Optional, Union

from bs4 import NavigableString, Tag

import transmogrifier.models as timdex
from transmogrifier.config import load_external_config
from transmogrifier.sources.transformer import Transformer

logger = logging.getLogger(__name__)


class Ead(Transformer):
    """EAD transformer."""

    def get_optional_fields(self, xml: Tag) -> Optional[dict]:
        """
        Retrieve optional TIMDEX fields from an EAD XML record.

        Overrides metaclass get_optional_fields() method.

        Args:
            xml: A BeautifulSoup Tag representing a single EAD XML record.
        """
        fields: dict = {}

        if collection_description := xml.metadata.find("archdesc", level="collection"):
            pass
        else:
            logger.error(
                f"Record ID {self.get_source_record_id(xml)} is missing archdesc element"
            )
            return None

        if collection_description_did := collection_description.did:
            pass
        else:
            logger.error(
                f"Record ID {self.get_source_record_id(xml)} is missing archdesc > did "
                "element"
            )
            return None

        control_access_elements = collection_description.find_all(
            "controlaccess", recursive=False
        )

        # alternate_titles

        # If the record has more than one main title, add extras to alternate_titles
        for index, title in enumerate(self.get_main_titles(xml)):
            if index > 0 and title:
                fields.setdefault("alternate_titles", []).append(
                    timdex.AlternateTitle(value=title)
                )

        # call_numbers field not used in EAD

        # citation
        if citation_element := collection_description.find(
            "prefercite", recursive=False
        ):
            if citation_value := self.create_string_from_mixed_value(
                citation_element, " ", ["head"]
            ):
                fields["citation"] = citation_value

        # content_type
        fields["content_type"] = ["Archival materials"]
        for control_access_element in control_access_elements:
            for content_type_element in control_access_element.find_all("genreform"):
                if content_type_value := self.create_string_from_mixed_value(
                    content_type_element,
                    " ",
                ):
                    fields["content_type"].append(content_type_value)

        # contents
        for arrangement_element in collection_description.find_all(
            "arrangement", recursive=False
        ):
            for arrangement_value in self.create_list_from_mixed_value(
                arrangement_element, ["head"]
            ):
                fields.setdefault("contents", []).append(arrangement_value)

        # contributors
        for origination_element in collection_description_did.find_all("origination"):
            for name_element in origination_element.find_all(True, recursive=False):
                if name_value := self.create_string_from_mixed_value(name_element, " "):
                    fields.setdefault("contributors", []).append(
                        timdex.Contributor(
                            value=name_value,
                            kind=origination_element.get("label") or None,
                            identifier=self.generate_name_identifier_url(name_element),
                        )
                    )
        # dates
        for date_element in collection_description_did.find_all("unitdate"):
            if date_value := self.create_string_from_mixed_value(
                date_element,
                " ",
            ):
                date_instance = timdex.Date()
                if "-" in date_value:
                    split = date_value.index("-")
                    date_instance.range = timdex.Date_Range(
                        gte=date_value[:split],
                        lte=date_value[split + 1 :],
                    )
                else:
                    date_instance.value = date_value
                date_instance.kind = date_element.get("datechar") or None
                date_instance.note = date_element.get("certainty") or None
                fields.setdefault("dates", []).append(date_instance)

        # edition field not used in EAD

        # file_formats field not used in EAD

        # format field not used in EAD

        # funding_information field not used in EAD. titlestmt > sponsor was considered
        # but did not fit the usage of this field in other sources.

        # holdings omitted pending discussion on how to map originalsloc and physloc

        # identifiers
        for id_element in collection_description_did.find_all(
            "unitid", recursive=False
        ):
            if id_value := self.create_string_from_mixed_value(
                id_element,
                " ",
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
                    " ",
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
            if note_element.name == "bibliography":
                subelement_tag = "bibref"
            else:
                subelement_tag = "p"
            note_value = []
            for subelement in note_element.find_all(subelement_tag, recursive=False):
                if subelement_value := self.create_string_from_mixed_value(
                    subelement,
                    " ",
                ):
                    note_value.append(subelement_value)
            if note_value:
                note_head_element = note_element.find("head", string=True)
                fields.setdefault("notes", []).append(
                    timdex.Note(
                        value=note_value,
                        kind=(
                            note_head_element.string
                            if note_head_element
                            else self.crosswalk_type_value(note_element.name)
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
                physical_description_element, " "
            ):
                physical_descriptions.append(physical_description_value)
        if physical_descriptions:
            fields["physical_description"] = "; ".join(physical_descriptions)

        # publication_frequency field not used in EAD

        # publication_information
        if publication_element := collection_description_did.find("repository"):
            if publication_value := self.create_string_from_mixed_value(
                publication_element, " "
            ):
                fields["publication_information"] = [publication_value]

        # related_items
        for related_item_element in collection_description.find_all(
            ["altformavail", "separatedmaterial"],
            recursive=False,
        ):
            if related_item_value := self.create_string_from_mixed_value(
                related_item_element, " ", ["head"]
            ):
                fields.setdefault("related_items", []).append(
                    timdex.RelatedItem(
                        description=related_item_value,
                        relationship=self.crosswalk_type_value(
                            related_item_element.name
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
                    subelement, " ", ["head"]
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
                rights_element, " ", ["head"]
            ):
                fields.setdefault("rights", []).append(
                    timdex.Rights(
                        description=rights_value,
                        kind=self.crosswalk_type_value(rights_element.name),
                    )
                )

        # subjects
        for control_access_element in control_access_elements:
            for subject_element in control_access_element.find_all(
                True, recursive=False
            ):
                if subject_value := self.create_string_from_mixed_value(
                    subject_element, " "
                ):
                    fields.setdefault("subjects", []).append(
                        timdex.Subject(
                            value=[subject_value],
                            kind=self.crosswalk_type_value(
                                subject_element.get("source") or None
                            ),
                        )
                    )

        # summary
        abstract_values = []
        for abstract_element in collection_description_did.find_all(
            "abstract", recursive=False
        ):
            if abstract_value := self.create_string_from_mixed_value(
                abstract_element, " "
            ):
                abstract_values.append(abstract_value)
        fields["summary"] = abstract_values or None

        return fields

    @classmethod
    def create_list_from_mixed_value(
        cls, xml_element: Tag, skipped_elements: Optional[list[str]] = None
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
        skipped_elements: Optional[list[str]] = None,
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

    @staticmethod
    def crosswalk_type_value(type_value: Optional[str]) -> Optional[str]:
        """
        Crosswalk type code to human-readable label.
        Args:
            type_value: A type value to be crosswalked.
        """
        type_crosswalk = load_external_config("config/aspace_type_crosswalk.json")
        if type_value in type_crosswalk:
            type_value = type_crosswalk[type_value]
        return type_value

    @classmethod
    def generate_name_identifier_url(cls, name_element: Tag) -> Optional[list]:
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
        else:
            return None

    @classmethod
    def get_main_titles(cls, xml: Tag) -> list[str]:
        """
        Retrieve main title(s) from an EAD XML record.

        Overrides metaclass get_main_titles() method.

        Args:
            xml: A BeautifulSoup Tag representing a single EAD XML record.
        """
        try:
            unit_titles = xml.metadata.find(
                "archdesc", level="collection"
            ).did.find_all("unittitle")
        except AttributeError:
            return []
        return [
            title
            for unit_title in unit_titles
            if (title := cls.create_string_from_mixed_value(unit_title, " ", ["num"]))
        ]

    @classmethod
    def get_source_record_id(cls, xml: Tag) -> str:
        """
        Get the source record ID from an EAD XML record.

        Overrides metaclass get_source_record_id() method.

        Args:
            xml: A BeautifulSoup Tag representing a single EAD XML record.
        """
        return xml.header.identifier.string.split("//")[1]

    @classmethod
    def parse_mixed_value(
        cls,
        item: Union[NavigableString, Tag],
        skipped_elements: Optional[list[str]] = None,
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
        if type(item) == NavigableString and item.strip():
            yield str(item.strip())
        elif type(item) == Tag and item.name not in skipped_elements:
            for child in item.children:
                yield from cls.parse_mixed_value(child, skipped_elements)
