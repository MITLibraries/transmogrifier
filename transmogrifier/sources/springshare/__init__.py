import logging
from typing import Dict, List, Optional

from bs4 import Tag
from dateutil.parser import parse as date_parser

import transmogrifier.models as timdex
from transmogrifier.sources.transformer import Transformer

logger = logging.getLogger(__name__)


class SpringshareOaiDc(Transformer):
    """Generic Springshare OAI DC transformer."""

    @property
    def source_name_singular(self):
        """
        Returns singular form of config.name for Springshare sources
            - e.g. "Libguides" -> "Libguide", "Research Databases" -> "Research Database"
                which is appropriate for the "links" type of "Libguide URL
        """
        return self.source_name.rstrip("s")

    def get_shared_optional_fields(
        self,
        xml: Tag,
    ) -> Optional[dict]:
        """
        Retrieve optional TIMDEX fields from a Springshare OAI DC XML record that
        are shared across libguides and researchdatabases sources.

        Args:
            xml: A BeautifulSoup Tag representing a single Springshare OAI DC XML record
        """

        fields: dict = {}

        # ensure dc:title and dc:identifier present and with content
        skip_record = False
        required_tags = ["dc:title", "dc:identifier"]
        for required_tag in required_tags:
            element = xml.find(required_tag)
            if element is None or element.string is None:
                skip_record = True
                logger.error("'%s' is missing or empty" % required_tag)
        if skip_record:
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

        # dates
        if date := xml.find("dc:date", string=True):
            # parse date format (e.g. "YYYY-MM-DD HH:MM:SS") not readily accepted
            # by OpenSearch, because of space instead of "T", and convert to ISO format
            date_iso_str = date_parser(date.string.strip()).isoformat()
            d = timdex.Date(value=date_iso_str, kind=None)
            fields.setdefault("dates", []).append(d)

        # format
        fields["format"] = "electronic resource"

        # identifiers
        fields.setdefault("identifiers", []).append(
            timdex.Identifier(
                value=xml.header.identifier.string,
                kind="OAI-PMH",
            )
        )

        # links, uses identifiers list retrieved for identifiers field
        identifiers = xml.find_all("dc:identifier")
        fields["links"] = [
            timdex.Link(
                kind=f"{self.source_name_singular} URL",
                text=f"{self.source_name_singular} URL",
                url=identifier.string,
            )
            for identifier in [i for i in identifiers if i.string]
        ] or None

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

        return fields

    @classmethod
    def get_main_titles(cls, xml: Tag) -> list[Tag]:
        """
        Retrieve main title(s) from a Springshare OAI DC XML record.

        Overrides metaclass get_main_titles() method.

        Args:
            xml: A BeautifulSoup Tag representing a single Springshare OAI DC XML record.
        """
        return [t for t in xml.find_all("dc:title")]

    @classmethod
    def get_source_record_id(cls, xml: Tag) -> str:
        """
        Get the source record ID from a Springshare OAI DC XML record.

        Overrides metaclass get_source_record_id() method.

        The URL path of the Springshare resource is used as the source record id, which
        results in a timdex record id like "libguides:materials" or
        "researchdatabases:llba".  This is preferred over the OAI-PMH identifier, a
        numeric value, which cannot be used to construct an accessible source link.

        Libguides example:
            "https://libguides.mit.edu/materials" -> "materials"

        AZ (Research Database) example:
            "https://libguides.mit.edu/llba" -> "llba"

        Args:
            xml: A BeautifulSoup Tag representing a single Springshare OAI DC XML record.
        """

        return xml.find("dc:identifier").string.split("/")[-1]
