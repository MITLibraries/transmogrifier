import logging

from bs4 import Tag  # type: ignore[import-untyped]

import transmogrifier.models as timdex
from transmogrifier.helpers import validate_date
from transmogrifier.sources.transformer import XMLTransformer

logger = logging.getLogger(__name__)


class OaiDc(XMLTransformer):
    """
    Generic OAI DC transformer.

    While technically this transformer COULD return a valid TIMDEX model, it is
    anticipated this will most likely get extended by a source-specific transformer.
    """

    def get_optional_fields(self, xml: Tag) -> dict | None:
        """
        Retrieve optional TIMDEX fields from a generic OAI DC XML record.

        Args:
            xml: A BeautifulSoup Tag representing a single OAI DC XML record
        """
        fields: dict = {}

        # extract source_record_id early for use and logging
        source_record_id = self.get_source_record_id(xml)

        # alternate_titles: not set in this transformation

        # call_numbers: not set in this transformation

        # citation: uses fallback get_citation() method

        # content_type
        fields["content_type"] = [self.source]

        # contents: not set in this transformation

        # contributors
        for creator in [c for c in xml.find_all("dc:creator") if c.string]:
            fields.setdefault("contributors", []).append(
                timdex.Contributor(
                    value=str(creator.string),
                    kind="Creator",
                )
            )

        # dates
        fields["dates"] = self.get_dates(source_record_id, xml) or None

        # edition: not set in this transformation

        # file_formats: not set in this transformation

        # format
        fields["format"] = "electronic resource"

        # funding_information: not set in this transformation

        # holdings: not set in this transformation

        # identifiers
        fields.setdefault("identifiers", []).append(
            timdex.Identifier(
                value=str(xml.header.identifier.string),
                kind="OAI-PMH",
            )
        )

        # languages: not set in this transformation

        # links
        fields["links"] = self.get_links(source_record_id, xml) or None

        # literary_form: not set in this transformation

        # locations: not set in this transformation

        # notes: not set in this transformation

        # numbering: not set in this transformation

        # physical_description: not set in this transformation

        # publication_frequency: not set in this transformation

        # publication_information
        fields["publication_information"] = [
            str(p.string) for p in xml.find_all("dc:publisher") if p.string
        ] or None

        # related_items: not set in this transformation

        # rights: not set in this transformation

        # subjects
        subjects_dict: dict[str, list[str]] = {}
        for subject in xml.metadata.find_all("dc:subject", string=True):
            subjects_dict.setdefault("Subject scheme not provided", []).append(
                str(subject.string)
            )
        fields["subjects"] = [
            timdex.Subject(value=value, kind=key) for key, value in subjects_dict.items()
        ] or None

        # summary
        # uses description list retrieved for notes field
        for description in [d for d in xml.find_all("dc:description") if d.string]:
            fields.setdefault("summary", []).append(str(description.string))

        return fields

    def get_dates(self, source_record_id: str, xml: Tag) -> list[timdex.Date]:
        """
        Method to get TIMDEX "dates" field.  This method broken out to allow subclasses
        to override.

        Return list of timdex.Date's if valid and present.

        Args:
            source_record_id: Source record id
            xml: A BeautifulSoup Tag representing a single OAI DC XML record.
        """
        dates = []
        if date_elements := xml.find_all("dc:date", string=True):
            for date in date_elements:
                date_str = str(date.string.strip())
                if validate_date(
                    date_str,
                    source_record_id,
                ):
                    dates.append(timdex.Date(value=date_str, kind="Unknown"))
        return dates

    def get_links(
        self, source_record_id: str, xml: Tag  # noqa: ARG002
    ) -> list[timdex.Link] | None:
        """
        Method to get TIMDEX "links" field. This method broken out to allow subclasses
        to override.

        Args:
            source_record_id: Source record id
            xml: A BeautifulSoup Tag representing a single OAI DC XML record.
        """
        return None

    @classmethod
    def get_main_titles(cls, xml: Tag) -> list[str]:
        """
        Retrieve main title(s) from a generic OAI DC XML record.

        Overrides metaclass get_main_titles() method.

        Args:
            xml: A BeautifulSoup Tag representing a single OAI DC XML record.
        """
        return [t.string for t in xml.find_all("dc:title", string=True)]

    @classmethod
    def get_source_record_id(cls, xml: Tag) -> str:
        """
        Use OAI-PMH header identifier.  It is anticipated this will likely need to get
        overridden by subclasses with a meaningful identifier.

        Overrides metaclass get_source_record_id() method.

        Args:
            xml: A BeautifulSoup Tag representing a single OAI DC XML record.
        """
        return xml.header.identifier.string.split(":")[-1]
