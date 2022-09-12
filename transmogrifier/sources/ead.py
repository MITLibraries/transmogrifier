import logging

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

        if collection_description := xml.metadata.find("archdesc"):
            pass
        else:
            raise ValueError("Record is missing archdesc element")

        collection_description_did = collection_description.find("did", recursive=False)

        # alternate_titles

        # If the record has more than one main title, add extras to alternate_titles
        for index, title in enumerate(self.get_main_titles(xml)):
            if index > 0 and title:
                fields.setdefault("alternate_titles", []).append(
                    timdex.AlternateTitle(value=title)
                )

        # contributors
        if collection_description_did:
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

        return fields

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
        main_titles = []
        if collection_description := xml.metadata.find("archdesc", level="collection"):
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
