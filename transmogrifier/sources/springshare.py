import logging
from typing import List, Optional

from bs4 import Tag
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

    def get_dates(self, xml: Tag) -> Optional[List[timdex.Date]]:
        """
        Overrides OaiDc's default get_dates() logic for Springshare records.

        In Springshare records the dc:date format is "YYYY-MM-DD HH:MM:SS", which is not
        readily acceptable by OpenSearch, because of space instead of "T".  This method
        parses the date and serializes to ISO format.

        Args:
            xml: A BeautifulSoup Tag representing a single OAI DC XML record.
        """

        # get source_record_id for use in date validation logging
        source_record_id = self.get_source_record_id(xml)

        dates = []
        if date := xml.find("dc:date", string=True):
            date_iso_str = date_parser(date.string.strip()).isoformat()
            if validate_date(
                date_iso_str,
                source_record_id,
            ):
                dates.append(timdex.Date(value=date_iso_str, kind=None))
        return dates or None

    def get_links(self, xml: Tag) -> List[timdex.Link]:
        """
        Overrides OaiDc's default get_links() logic for Springshare records.

        Args:
            xml: A BeautifulSoup Tag representing a single OAI DC XML record.
        """

        identifier = xml.find("dc:identifier")
        singular_source_name = self.source_name.rstrip("s")
        return [
            timdex.Link(
                kind=f"{singular_source_name} URL",
                text=f"{singular_source_name} URL",
                url=identifier.string,
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

        return xml.find("dc:identifier").string.split("/")[-1]
