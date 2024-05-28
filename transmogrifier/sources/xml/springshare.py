import logging

from bs4 import Tag  # type: ignore[import-untyped]
from dateutil.parser import ParserError
from dateutil.parser import parse as date_parser

import transmogrifier.models as timdex
from transmogrifier.exceptions import SkippedRecordEvent
from transmogrifier.helpers import validate_date
from transmogrifier.sources.xml.oaidc import OaiDc

logger = logging.getLogger(__name__)


class SpringshareOaiDc(OaiDc):
    """
    Springshare transformer that extends generic OAI DC transformer.

    This transformer is used for:
        - libguides
        - researchdatabases
    """

    @classmethod
    def get_dates(cls, source_record: Tag) -> list[timdex.Date] | None:
        """
        Overrides OaiDc's default get_dates() logic for Springshare records.

        In Springshare records the dc:date format is "YYYY-MM-DD HH:MM:SS", which is not
        readily acceptable by OpenSearch, because of space instead of "T".  This method
        parses the date and serializes to ISO format.

        Additionally, only a single date will is expected.

        Args:
            source_record: A BeautifulSoup Tag representing a single OAI DC record in XML.
        """
        dates = []
        source_record_id = cls.get_source_record_id(source_record)
        if date := source_record.find("dc:date", string=True):
            try:
                date_iso_str = date_parser(str(date.string).strip()).isoformat()
                if validate_date(
                    date_iso_str,
                    source_record_id,
                ):
                    dates.append(timdex.Date(value=date_iso_str, kind="Created"))
            except ParserError as e:
                logger.debug(
                    "Record ID %s has a date that cannot be parsed: %s",
                    source_record_id,
                    str(e),
                )
        return dates or None

    def get_links(self, source_record: Tag) -> list[timdex.Link] | None:
        """
        Overrides OaiDc's default get_links() logic for Springshare records.

        Args:
            source_record: A BeautifulSoup Tag representing a single OAI DC record in XML.
        """
        links = []
        source_record_id = self.get_source_record_id(source_record)
        if identifier := source_record.find("dc:identifier", string=True):
            singular_source_name = self.source_name.rstrip("s")
            links.append(
                timdex.Link(
                    kind=f"{singular_source_name} URL",
                    text=f"{singular_source_name} URL",
                    url=str(identifier.string),
                )
            )

        logger.debug(
            "Record ID %s has links that cannot be generated: missing dc:identifier",
            source_record_id,
        )
        return links or None

    @classmethod
    def get_source_link(
        cls,
        _source_base_url: str,
        _source_record_id: str,
        source_record: Tag,
    ) -> str:
        """
        Override for default source_link behavior.

        Springshare resources contain the source link in their dc:identifier fields.
        However, this cannot be reliably split and combined with the source base url,
        as this either provides poorly formed timdex record ids OR source links that
        do not work.

        Example libguides OAI identifier and <dc:identifier>:
            - oai:libguides.com:guides/175846, https://libguides.mit.edu/materials
            - oai:libguides.com:guides/175847, https://libguides.mit.edu/c.php?g=175847

        Example researchdatabases OAI identifier and <dc:identifier>:
            - oai:libguides.com:az/65257807, https://libguides.mit.edu/llba

        It is preferable to split the OAI header identifier and use this as the TIMDEX
        record id, but then take the dc:identifier wholesale and use this for the source
        link.

        Args:
            source_record: A BeautifulSoup Tag representing a single OAI DC record in XML.
        """
        if source_link := source_record.find("dc:identifier", string=True):
            return str(source_link.string)
        message = (
            "Record skipped because 'source_link' could not be derived. "
            "The 'identifier' was either missing from the header element or blank."
        )
        raise SkippedRecordEvent(message)
