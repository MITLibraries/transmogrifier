import logging
from typing import Dict, List, Optional

from bs4 import Tag

import transmogrifier.models as timdex
from transmogrifier.helpers import validate_date
from transmogrifier.sources.transformer import Transformer

logger = logging.getLogger(__name__)


class OaiDc(Transformer):
    """
    Generic OAI DC transformer.

    While technically this transformer COULD return a valid TIMDEX model, it is
    anticipated this will most likely get extended by a source-specific transformer.
    """

    def get_optional_fields(self, xml: Tag) -> Optional[dict]:
        """
        Retrieve optional TIMDEX fields from a generic OAI DC XML record.

        Args:
            xml: A BeautifulSoup Tag representing a single OAI DC XML record
        """

        fields: dict = {}

        # skip record if required dc:title and/or dc:identifier without values
        # NOTE: follows same pattern of skipping records as other transforms, but could be
        #  opportunity to introduce "SkippedRecords" exception and handling
        title = xml.find("dc:title", string=True)
        identifier = xml.find("dc:identifier", string=True)
        if None in [title, identifier]:
            logger.error("dc:title or dc:identifier is missing or blank")
            return None

        # citation
        title = xml.find("dc:title")
        identifier = xml.find("dc:identifier")
        fields["citation"] = f"{title.string}. {self.source_name}. {identifier.string}"

        # content_type
        fields["content_type"] = [self.source]

        # contributors
        for creator in [c for c in xml.find_all("dc:creator") if c.string]:
            fields.setdefault("contributors", []).append(
                timdex.Contributor(
                    value=creator.string,
                    kind="Creator",
                )
            )

        # format
        fields["format"] = "electronic resource"

        # identifiers
        fields.setdefault("identifiers", []).append(
            timdex.Identifier(
                value=xml.header.identifier.string,
                kind="OAI-PMH",
            )
        )

        # publication_information
        fields["publication_information"] = [
            p.string for p in xml.find_all("dc:publisher") if p.string
        ] or None

        # subjects
        subjects_dict: Dict[str, List[str]] = {}
        for subject in xml.metadata.find_all("dc:subject", string=True):
            subjects_dict.setdefault("Subject scheme not provided", []).append(
                subject.string
            )
        fields["subjects"] = [
            timdex.Subject(value=value, kind=key)
            for key, value in subjects_dict.items()
        ] or None

        # summary, uses description list retrieved for notes field
        descriptions = xml.find_all("dc:description")
        for description in [d for d in descriptions if d.string]:
            fields.setdefault("summary", []).append(description.string)

        # dates
        fields["dates"] = self.get_dates(xml)

        # links
        fields["links"] = self.get_links(xml)

        return fields

    def get_dates(self, xml: Tag) -> Optional[List[timdex.Date]]:
        """
        Method to get TIMDEX "dates" field.  This method broken out to allow subclasses
        to override.

        Return list of timdex.Date's if valid and present.

        Args:
            xml: A BeautifulSoup Tag representing a single OAI DC XML record.
        """

        # get source_record_id for use in date validation logging
        source_record_id = self.get_source_record_id(xml)

        dates = []
        if date_elements := xml.find_all("dc:date", string=True):
            for date in date_elements:
                date_str = str(date.string.strip())
                if validate_date(
                    date_str,
                    source_record_id,
                ):
                    dates.append(timdex.Date(value=date_str))
        return dates or None

    def get_links(self, xml: Tag) -> Optional[List[timdex.Link]]:
        """
        Method to get TIMDEX "links" field. This method broken out to allow subclasses
        to override.

        Args:
            xml: A BeautifulSoup Tag representing a single OAI DC XML record.
        """

        return None

    @classmethod
    def get_main_titles(cls, xml: Tag) -> list[Tag]:
        """
        Retrieve main title(s) from a generic OAI DC XML record.

        Overrides metaclass get_main_titles() method.

        Args:
            xml: A BeautifulSoup Tag representing a single OAI DC XML record.
        """
        return [t for t in xml.find_all("dc:title")]

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
