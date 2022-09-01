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
        for alternate_title_value in [
            alternate_title
            for alternate_title_elem in xml.find_all("subtitle")
            if (
                alternate_title := " ".join(
                    string for string in alternate_title_elem.stripped_strings
                )
            )
        ]:
            fields.setdefault("alternate_titles", []).append(
                timdex.AlternateTitle(
                    value=alternate_title_value,
                    kind="subtitle",
                )
            )
        # If the record has more than one main title, add extras to alternate_titles
        for index, title in enumerate(self.get_main_titles(xml)):
            if index > 0 and title:
                fields.setdefault("alternate_titles", []).append(
                    timdex.AlternateTitle(value=title)
                )

        # call_numbers field not used in EAD

        # citation
        fields["citation"] = (
            " ".join(
                string
                for citation_elem in xml.find_all("prefercite")
                for string in citation_elem.stripped_strings
            )
            or None
        )

        # content_type
        if content_types_value := [
            content_types
            for content_types_elem in xml.find_all("materialspec")
            if (
                content_types := " ".join(
                    string for string in content_types_elem.stripped_strings
                )
            )
        ]:
            fields["content_type"] = content_types_value

        # contents
        if contents_value := [
            contents
            for contents_elem in xml.find_all("scopecontent")
            if contents_elem.parent.name == "archdesc"
            if (
                contents := " ".join(
                    string for string in contents_elem.stripped_strings
                )
            )
        ]:
            fields["contents"] = contents_value

        # contributors
        for contributor_elem in [
            orig_child
            for orig_elem in xml.find_all("origination")
            for orig_child in orig_elem.contents
            if orig_elem.parent.parent.name == "archdesc" and type(orig_child) == Tag
        ]:
            if contributor_value := " ".join(
                string for string in contributor_elem.stripped_strings
            ):
                fields.setdefault("contributors", []).append(
                    timdex.Contributor(
                        value=contributor_value,
                        kind=contributor_elem.parent.get("label"),
                        identifier=[contributor_elem.get("authfilenumber")]
                        if contributor_elem.get("authfilenumber")
                        else None,
                    )
                )

        # dates
        for date_elem in [
            date_elem
            for date_elem in chain(
                xml.find_all("unitdate"), xml.find_all("unitdatestructured")
            )
            if date_elem.parent.parent.name == "archdesc"
        ]:
            if date_value := " ".join(string for string in date_elem.stripped_strings):
                fields.setdefault("dates", []).append(
                    timdex.Date(
                        value=date_value,
                        kind=date_elem.get("type"),
                    )
                )

        # edition field not used in EAD

        # file_formats field not used in EAD

        # format
        fields["format"] = "electronic resource"

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

        # holdings field not used in EAD

        # identifiers
        for id_value in [
            id
            for id_elem in xml.find_all("unitid")
            if id_elem.parent.parent.name == "archdesc"
            if (id := " ".join(string for string in id_elem.stripped_strings))
        ]:
            fields.setdefault("identifiers", []).append(
                timdex.Identifier(
                    value=id_value,
                )
            )

        # languages
        if languages := xml.find_all("language", string=True):
            fields["languages"] = [
                lang_elem.string
                for lang_elem in languages
                if lang_elem.parent.parent.parent.name == "archdesc"
            ] or None

        # links
        for link_elem in [
            link_elem
            for link_elem in xml.find_all("dao")
            if link_elem.get("xlink:href")
        ]:
            fields.setdefault("links", []).append(
                timdex.Link(
                    text=link_elem.get("xlink:title"),
                    url=link_elem.get("xlink:href"),
                )
            )

        # literary_form field not used in EAD

        # locations
        for location_value in [
            location
            for location_elem in chain(
                xml.find_all("originalsloc"),
                xml.find_all("physloc"),
            )
            if location_elem.parent.name == "archdesc"
            if (
                location := " ".join(
                    string for string in location_elem.stripped_strings
                )
            )
        ]:
            fields.setdefault("locations", []).append(
                timdex.Location(value=location_value)
            )

        # notes
        for note_elem in [
            note_elem
            for note_elem in chain(
                xml.find_all("acqinfo"),
                xml.find_all("appraisal"),
                xml.find_all("bibliography"),
                xml.find_all("bioghist"),
                xml.find_all("custodhist"),
                xml.find_all("processinfo"),
            )
            if note_elem.parent.name == "archdesc"
        ]:
            if note_value := " ".join(string for string in note_elem.stripped_strings):
                fields.setdefault("notes", []).append(
                    timdex.Note(
                        value=[note_value],
                        kind=note_elem.name,
                    )
                )

        # numbering field not used in EAD

        # physical_description
        fields["physical_description"] = (
            " ".join(
                string
                for physdesc_elem in [
                    physdesc_elem
                    for physdesc_elem in chain(
                        xml.find_all("physdesc"),
                        xml.find_all("physdescstructured"),
                    )
                    if physdesc_elem.parent.parent.name == "archdesc"
                ]
                for string in physdesc_elem.stripped_strings
            )
            or None
        )

        # publication_frequency field not used in EAD

        # publication_information
        if publication_elem := xml.find("publicationstmt"):
            if publication_value := " ".join(
                string for string in publication_elem.stripped_strings
            ):
                fields["publication_information"] = [publication_value]

        # related_items
        for related_item_elem in chain(
            [
                related_item_elem
                for related_item_elem in chain(
                    xml.find_all("altformavail"),
                    xml.find_all("relatedmaterial"),
                    xml.find_all("otherfindaid"),
                )
                if related_item_elem.parent.name == "archdesc"
            ],
            [
                related_item_elem
                for related_item_elem in chain(
                    xml.find_all("relation"),
                )
                if related_item_elem.parent.parent.name == "archdesc"
            ],
        ):
            if related_item_value := " ".join(
                string for string in related_item_elem.stripped_strings
            ):
                fields.setdefault("related_items", []).append(
                    timdex.RelatedItem(
                        description=related_item_value,
                        relationship=related_item_elem.name,
                    )
                )

        # rights
        for rights_elem in [
            rights_elem
            for rights_elem in chain(
                xml.find_all("accessrestrict"),
                xml.find_all("legalstatus"),
                xml.find_all("userestrict"),
            )
            if rights_elem.parent.name == "archdesc"
        ]:
            if rights_value := " ".join(
                string for string in rights_elem.stripped_strings
            ):
                fields.setdefault("rights", []).append(
                    timdex.Rights(description=rights_value, kind=rights_elem.name)
                )

        # subjects
        for subject_elem in [
            ca_child
            for ca_elem in xml.find_all("controlaccess")
            for ca_child in ca_elem.contents
            if ca_elem.parent.name == "archdesc" and type(ca_child) == Tag
        ]:
            if subject_value := " ".join(
                string for string in subject_elem.stripped_strings
            ):
                fields.setdefault("subjects", []).append(
                    timdex.Subject(
                        value=[subject_value],
                        kind=subject_elem.get("source"),
                    )
                )

        # summary
        if abstract_value := [
            abstract
            for abstract_elem in xml.find_all("abstract")
            if abstract_elem.parent.parent.name == "archdesc"
            if (
                abstract := " ".join(
                    string for string in abstract_elem.stripped_strings
                )
            )
        ]:
            fields["summary"] = abstract_value

        return fields

    @classmethod
    def get_main_titles(cls, xml: Tag) -> list[str]:
        """
        Retrieve main title(s) from an EAD XML record.

        Overrides metaclass get_main_titles() method.

        Args:
            xml: A BeautifulSoup Tag representing a single EAD XML record.
        """
        return [
            titleproper_value
            for titleproper_elem in xml.find_all("titleproper")
            if (
                titleproper_value := ", ".join(
                    string for string in titleproper_elem.stripped_strings
                )
            )
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
