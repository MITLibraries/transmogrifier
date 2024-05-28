import logging

from bs4 import Tag  # type: ignore[import-untyped]

import transmogrifier.models as timdex
from transmogrifier.exceptions import SkippedRecordEvent
from transmogrifier.helpers import validate_date
from transmogrifier.sources.xmltransformer import XMLTransformer

logger = logging.getLogger(__name__)


class OaiDc(XMLTransformer):
    """
    Generic OAI DC transformer.

    While technically this transformer COULD return a valid TIMDEX model, it is
    anticipated this will most likely get extended by a source-specific transformer.
    """

    def get_optional_fields(self, source_record: Tag) -> dict | None:
        """
        Retrieve optional TIMDEX fields from a generic OAI DC XML record.

        Args:
            source_record: A BeautifulSoup Tag representing a single OAI DC record in XML.
        """
        fields: dict = {}

        # alternate_titles: not set in this transformation

        # call_numbers: not set in this transformation

        # citation: uses fallback get_citation() method

        # content_type
        fields["content_type"] = self.get_content_type()

        # contents: not set in this transformation

        # contributors
        fields["contributors"] = self.get_contributors(source_record)

        # dates
        fields["dates"] = self.get_dates(source_record)

        # edition: not set in this transformation

        # file_formats: not set in this transformation

        # format
        fields["format"] = self.get_format()

        # funding_information: not set in this transformation

        # holdings: not set in this transformation

        # identifiers
        fields["identifiers"] = self.get_identifiers(source_record)

        # languages: not set in this transformation

        # links
        fields["links"] = self.get_links(source_record)

        # literary_form: not set in this transformation

        # locations: not set in this transformation

        # notes: not set in this transformation

        # numbering: not set in this transformation

        # physical_description: not set in this transformation

        # publication_frequency: not set in this transformation

        # publishers
        fields["publishers"] = self.get_publishers(source_record)

        # related_items: not set in this transformation

        # rights: not set in this transformation

        # subjects
        fields["subjects"] = self.get_subjects(source_record)

        # summary
        fields["summary"] = self.get_summary(source_record)
        return fields

    def get_content_type(self) -> list[str]:
        return [self.source]

    @classmethod
    def get_contributors(cls, source_record: Tag) -> list[timdex.Contributor] | None:
        return [
            timdex.Contributor(value=str(creator.string), kind="Creator")
            for creator in source_record.find_all("dc:creator", string=True)
        ] or None

    @classmethod
    def get_dates(cls, source_record: Tag) -> list[timdex.Date] | None:
        """
        Method to get TIMDEX "dates" field.  This method broken out to allow subclasses
        to override.

        Return list of timdex.Date's if valid and present.

        Args:
            source_record: A BeautifulSoup Tag representing a single OAI DC record in XML.

        """
        dates = []
        source_record_id = cls.get_source_record_id(source_record)
        for date in source_record.find_all("dc:date", string=True):
            date_value = str(date.string.strip())
            if validate_date(date_value, source_record_id):
                dates.append(timdex.Date(value=date_value, kind="Unknown"))
        return dates or None

    @classmethod
    def get_format(cls) -> str:
        return "electronic resource"

    @classmethod
    def get_identifiers(cls, source_record: Tag) -> list[timdex.Identifier] | None:
        identifiers = []
        if identifier := source_record.header.find("identifier", string=True):
            identifiers.append(
                timdex.Identifier(
                    value=str(identifier.string),
                    kind="OAI-PMH",
                )
            )
        return identifiers or None

    def get_links(
        self,
        _source_record: Tag,
    ) -> list[timdex.Link] | None:
        """
        Method to get TIMDEX "links" field. This method broken out to allow subclasses
        to override.

        Args:
            source_record: A BeautifulSoup Tag representing a single OAI DC record in XML.
        """
        return [] or None

    @classmethod
    def get_publishers(cls, source_record: Tag) -> list[timdex.Publisher] | None:
        return [
            timdex.Publisher(name=str(publisher.string))
            for publisher in source_record.find_all("dc:publisher", string=True)
        ] or None

    @classmethod
    def get_subjects(cls, source_record: Tag) -> list[timdex.Subject] | None:
        subjects = [
            str(subject.string)
            for subject in source_record.find_all("dc:subject", string=True)
        ]
        if subjects:
            return [timdex.Subject(value=subjects, kind="Subject scheme not provided")]
        return [] or None

    @classmethod
    def get_summary(cls, source_record: Tag) -> list[str] | None:
        return [
            str(description.string)
            for description in source_record.find_all("dc:description", string=True)
        ] or None

    @classmethod
    def get_main_titles(cls, source_record: Tag) -> list[str]:
        """
        Retrieve main title(s) from a generic OAI DC XML record.

        Overrides metaclass get_main_titles() method.

        Args:
            source_record: A BeautifulSoup Tag representing a single OAI DC record in XML.
        """
        return [
            str(title.string) for title in source_record.find_all("dc:title", string=True)
        ]

    @classmethod
    def get_source_record_id(cls, source_record: Tag) -> str:
        """
        Use OAI-PMH header identifier.  It is anticipated this will likely need to get
        overridden by subclasses with a meaningful identifier.

        Overrides metaclass get_source_record_id() method.

        Args:
            source_record: A BeautifulSoup Tag representing a single OAI DC record in XML.
        """
        if identifier := source_record.header.find("identifier", string=True):
            return str(identifier.string).split(":")[-1]
        message = (
            "Record skipped because 'source_record_id' could not be derived. "
            "The 'identifier' was either missing from the header element or blank."
        )
        raise SkippedRecordEvent(message)
