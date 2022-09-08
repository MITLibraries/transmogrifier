import logging
from itertools import chain

from bs4 import Tag

import transmogrifier.models as timdex
from transmogrifier.sources.transformer import Transformer

logger = logging.getLogger(__name__)


class Ead(Transformer):
    """EAD transformer."""

    def get_optional_fields(self, xml: Tag) -> dict:
        """
        Retrieve optional TIMDEX fields from an EAD XML record.

        Overrides metaclass get_optional_fields() method.

        Args:
            xml: A BeautifulSoup Tag representing a single EAD XML record.
        """
        fields: dict = {}

        # alternate_titles
        # If the record has more than one main title, add extras to alternate_titles
        for index, title in enumerate(self.get_main_titles(xml)):
            if index > 0 and title:
                fields.setdefault("alternate_titles", []).append(
                    timdex.AlternateTitle(value=title)
                )

        # funding_information
        for funder_value in [
            funder
            for funder_elem in xml.find_all("sponsor")
            if (funder := " ".join(string for string in funder_elem.stripped_strings))
        ]:
            fields.setdefault("funding_information", []).append(
                timdex.Funder(
                    funder_name=funder_value,
                )
            )

        # publication_information
        if publication_elem := xml.find("publicationstmt"):
            if publication_value := " ".join(
                string for string in publication_elem.stripped_strings
            ):
                fields["publication_information"] = [publication_value]

        # call_numbers field not used in EAD

        # edition field not used in EAD

        # file_formats field not used in EAD

        # format

        # links, omitted pending decision on duplicating source_link

        # literary_form field not used in EAD

        # numbering field not used in EAD

        # publication_frequency field not used in EAD

        # fields found in archdesc element

        collection_description = xml.metadata.find("archdesc", level="collection")
        if collection_description:

            # citation
            if citation_elem := collection_description.find("prefercite"):
                fields["citation"] = self.create_string_from_mixed_value(citation_elem)

            # content_type
            if content_types_value := [
                content_types
                for content_types_elem in collection_description.find_all("genreform")
                if (
                    content_types := " ".join(
                        string for string in content_types_elem.stripped_strings
                    )
                )
            ]:
                fields["content_type"] = content_types_value
                fields["content_type"].append("Archival materials")

            # contents
            for arrangement_value in [
                arrangement
                for arrangement_elem in collection_description.find_all(
                    "arrangement", recursive=False
                )
                if (
                    arrangement := self.create_string_from_mixed_value(arrangement_elem)
                )
            ]:
                fields.setdefault("contents", []).append(arrangement_value)

            # holdings
            for holdings_value in [
                holding
                for holding_elem in chain(
                    collection_description.find_all("originalsloc", recursive=False),
                    collection_description.find_all("physloc", recursive=False),
                )
                if (
                    holding := " ".join(
                        string for string in holding_elem.stripped_strings
                    )
                )
            ]:
                fields.setdefault("holdings", []).append(
                    timdex.Holding(note=holdings_value)
                )

            # languages
            if languages := collection_description.find("langmaterial"):
                fields["languages"] = [
                    "".join(lang_elem for lang_elem in languages.stripped_strings)
                ] or None

            # locations
            for location_value in [
                location
                for location_elem in collection_description.find_all("geogname")
                if (location := self.create_string_from_mixed_value(location_elem))
            ]:
                print(location_value)
                fields.setdefault("locations", []).append(
                    timdex.Location(value=location_value)
                )

            # notes
            for note_elem in [
                note_elem
                for note_elem in chain(
                    collection_description.find_all("acqinfo", recursive=False),
                    collection_description.find_all("appraisal", recursive=False),
                    collection_description.find_all("bibliography", recursive=False),
                    collection_description.find_all("bioghist", recursive=False),
                    collection_description.find_all("custodhist", recursive=False),
                    collection_description.find_all("processinfo", recursive=False),
                    collection_description.find_all("scopecontent", recursive=False),
                )
            ]:
                if note_value := self.create_string_from_mixed_value(note_elem):
                    fields.setdefault("notes", []).append(
                        timdex.Note(
                            value=[note_value],
                            kind=self.crosswalk_type_value(note_elem.name),
                        )
                    )

            # related_items
            for related_item_elem in [
                related_item_elem
                for related_item_elem in chain(
                    collection_description.find_all("altformavail", recursive=False),
                    collection_description.find_all("relatedmaterial", recursive=False),
                    collection_description.find_all("otherfindaid", recursive=False),
                    collection_description.find_all("relation"),
                    collection_description.find_all(
                        "separatedmaterial", recursive=False
                    ),
                )
            ]:
                if related_item_value := self.create_string_from_mixed_value(
                    related_item_elem
                ):
                    fields.setdefault("related_items", []).append(
                        timdex.RelatedItem(
                            description=related_item_value,
                            relationship=self.crosswalk_type_value(
                                related_item_elem.name
                            ),
                        )
                    )

            # rights
            for rights_elem in [
                rights_elem
                for rights_elem in chain(
                    collection_description.find_all("accessrestrict", recursive=False),
                    collection_description.find_all("legalstatus", recursive=False),
                    collection_description.find_all("userestrict", recursive=False),
                )
            ]:
                if rights_value := self.create_string_from_mixed_value(rights_elem):
                    fields.setdefault("rights", []).append(
                        timdex.Rights(
                            description=rights_value,
                            kind=self.crosswalk_type_value(rights_elem.name),
                        )
                    )

            # subjects
            for subject_elem in [
                ca_child
                for ca_elem in collection_description.find_all(
                    "controlaccess", recursive=False
                )
                for ca_child in ca_elem.contents
                if type(ca_child) == Tag
            ]:
                if subject_value := " ".join(
                    string for string in subject_elem.stripped_strings
                ):
                    fields.setdefault("subjects", []).append(
                        timdex.Subject(
                            value=[subject_value],
                            kind=self.crosswalk_type_value(subject_elem.get("source")),
                        )
                    )

            # fields found in archdesc > did element
            collection_description_did = collection_description.find(
                "did", recursive=False
            )
            if collection_description_did:

                # contributors
                for contributor_elem in [
                    orig_child
                    for orig_elem in collection_description_did.find_all(
                        "origination", recursive=False
                    )
                    for orig_child in orig_elem.contents
                    if type(orig_child) == Tag
                ]:
                    if contributor_value := " ".join(
                        string for string in contributor_elem.stripped_strings
                    ):
                        fields.setdefault("contributors", []).append(
                            timdex.Contributor(
                                value=contributor_value,
                                kind=contributor_elem.parent.get("label"),
                                identifier=[
                                    self.generate_name_identifier_url(contributor_elem)
                                ]
                                if contributor_elem.get("authfilenumber")
                                else None,
                            )
                        )

                # dates
                for date_elem in [
                    date_elem
                    for date_elem in chain(
                        collection_description_did.find_all("unitdate"),
                        collection_description_did.find_all("unitdatestructured"),
                    )
                ]:
                    if date_value := " ".join(
                        string for string in date_elem.stripped_strings
                    ):
                        fields.setdefault("dates", []).append(
                            timdex.Date(
                                value=date_value,
                                kind=date_elem.get("type"),
                            )
                        )

                # identifiers
                for id_value in [
                    id
                    for id_elem in collection_description_did.find_all("unitid")
                    if (id := " ".join(string for string in id_elem.stripped_strings))
                ]:
                    fields.setdefault("identifiers", []).append(
                        timdex.Identifier(
                            value=id_value,
                        )
                    )

                # physical_description
                if physical_description_value := (
                    " ".join(
                        string
                        for physdesc_elem in [
                            physdesc_elem
                            for physdesc_elem in collection_description_did.find_all(
                                "physdesc", recursive=False
                            )
                        ]
                        for string in physdesc_elem.stripped_strings
                        if string
                    )
                ):
                    fields["physical_description"] = physical_description_value

                # summary
                if abstract_value := [
                    abstract
                    for abstract_elem in collection_description_did.find_all(
                        "abstract", recursive=False
                    )
                    if (
                        abstract := " ".join(
                            string for string in abstract_elem.stripped_strings
                        )
                    )
                ]:
                    fields["summary"] = abstract_value

        return fields

    @classmethod
    def create_string_from_mixed_value(cls, xml_element: Tag) -> str:
        """
        Create a string from an XML element value that contains a mix of strings
        and XML elements. This method is used for fields where .stripped_strings
        pulls in unnecessary formatting.

        Args:
            xml_element: An XML element that may contain a value consisting of
            strings and XML elements.

        """
        return " ".join(
            [
                string
                for contents_child in xml_element.contents
                for string in contents_child.stripped_strings
                if type(contents_child) == Tag and contents_child.name != "head"
                if string
            ]
        )

    @classmethod
    def crosswalk_type_value(cls, type_value: str) -> str:
        """
        Crosswalk type code to human-readable label.

        Args:
            type_value: A type value to be crosswalked.
        """
        type_crosswalk = {
            "aat": "Art & Architecture Thesaurus",
            "accessrestrict": "Conditions Governing Access",
            "altformavail": "Alternative Form Available",
            "acqinfo": "Acquisition Information",
            "appraisal": "Appraisal",
            "bibliography": "Bibliography",
            "bioghist": "Biographical and Historical Note",
            "custodhist": "Custodial History",
            "gmgpc": (
                "Thesaurus for Graphic Materials II: Genre and Physical Characteristic "
                "Terms"
            ),
            "lcnaf": "Library of Congress Name Authority File",
            "lcsh": "Library of Congress Subject Headings",
            "legalstatus": "Legal Status",
            "naf": "Library of Congress Name Authority File",
            "otherfindaid": "Other Finding Aid",
            "processinfo": "Processing Information",
            "relatedmaterial": "Related Material",
            "relation": "Relation",
            "separatedmaterial": "Separated Material",
            "scopecontent": "Scope and Contents Note",
            "snac": "Social Networks and Archival Context",
            "tucua": "Thesaurus for Use in College and University Archives",
            "userestrict": "Conditions Governing Use",
            "viaf": "Virtual International Authority File",
        }
        if type_value in type_crosswalk:
            type_value = type_crosswalk[type_value]
        return type_value

    @classmethod
    def generate_name_identifier_url(cls, name_element: Tag) -> str:
        """
        Generate a full name identifier URL with the specified scheme.

        Args:
            name_element: A BeautifulSoup Tag representing an EAD
                name XML field.
        """
        source = name_element.get("source")
        if source in ["lcnaf", "naf"]:
            base_url = "https://lccn.loc.gov/"
        elif source == "snac":
            base_url = "https://snaccooperative.org/view/"
        elif source == "viaf":
            base_url = "http://viaf.org/viaf/"
        else:
            base_url = ""
        return base_url + name_element.get("authfilenumber")

    @classmethod
    def get_main_titles(cls, xml: Tag) -> list[str]:
        """
        Retrieve main title(s) from an EAD XML record.

        Overrides metaclass get_main_titles() method.

        Args:
            xml: A BeautifulSoup Tag representing a single EAD XML record.
        """
        collection_description = xml.metadata.find("archdesc", level="collection")
        if collection_description:
            collection_description_did = collection_description.find("did")
            if collection_description_did:
                main_titles = [
                    unittitle_value
                    for unittitle_elem in collection_description_did.find_all(
                        "unittitle", recursive=False
                    )
                    if (
                        unittitle_value := ", ".join(
                            string for string in unittitle_elem.stripped_strings
                        )
                    )
                ]
        else:
            main_titles = []
        return main_titles

    @classmethod
    def get_source_record_id(cls, xml: Tag) -> str:
        """
        Get the source record ID from an EAD XML record.

        Overrides metaclass get_source_record_id() method.

        Args:
            xml: A BeautifulSoup Tag representing a single EAD XML record.
        """
        return xml.header.identifier.string.split("//")[1]
