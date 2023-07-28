import logging
from typing import List, Optional

from bs4 import Tag
from dateutil.parser import ParserError
from dateutil.parser import parse as date_parser

import transmogrifier.models as timdex
from transmogrifier.helpers import validate_date
from transmogrifier.sources.oaidc import OaiDc

logger = logging.getLogger(__name__)


class SpringshareOaiDc(OaiDc):
    """
    Springshare transformer that extends generic OAI DC transformer.

    This transformer is used for:
        - libguides
        - researchdatabases
    """

    def get_dates(self, source_record_id: str, xml: Tag) -> Optional[List[timdex.Date]]:
        """
        Overrides OaiDc's default get_dates() logic for Springshare records.

        In Springshare records the dc:date format is "YYYY-MM-DD HH:MM:SS", which is not
        readily acceptable by OpenSearch, because of space instead of "T".  This method
        parses the date and serializes to ISO format.

        Additionally, only a single date will is expected.

        Args:
            source_record_id: Source record id
            xml: A BeautifulSoup Tag representing a single OAI DC XML record.
        """

        dates = []
        if date := xml.find("dc:date", string=True):
            try:
                date_iso_str = date_parser(str(date.string).strip()).isoformat()
            except ParserError as e:
                logger.debug(
                    "Record ID %s has a date that cannot be parsed: %s",
                    source_record_id,
                    str(e),
                )
                return None
            if validate_date(
                date_iso_str,
                source_record_id,
            ):
                dates.append(timdex.Date(value=date_iso_str, kind=None))
        return dates or None

    def get_links(self, source_record_id: str, xml: Tag) -> Optional[List[timdex.Link]]:
        """
        Overrides OaiDc's default get_links() logic for Springshare records.

        Args:
            source_record_id: Source record id
            xml: A BeautifulSoup Tag representing a single OAI DC XML record.
        """

        identifier = xml.find("dc:identifier")
        if identifier is None or identifier.string is None:
            logger.debug(
                "Record ID %s has links that cannot be generated: missing dc:identifier",
                source_record_id,
            )
            return None
        singular_source_name = self.source_name.rstrip("s")
        return [
            timdex.Link(
                kind=f"{singular_source_name} URL",
                text=f"{singular_source_name} URL",
                url=str(identifier.string),
            )
        ]

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

        return str(xml.find("dc:identifier").string).split("/")[-1]
