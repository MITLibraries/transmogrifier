import logging
from collections.abc import Iterator
from datetime import UTC, datetime

import smart_open  # type: ignore[import-untyped]
from bs4 import BeautifulSoup, Tag
from lxml import etree

from transmogrifier.config import LAST_AZ_IDENTIFIERS_PATH
from transmogrifier.helpers import LibGuidesAPIClient
from transmogrifier.sources.xml.springshare import SpringshareOaiDc

logger = logging.getLogger(__name__)


class ResearchDatabases(SpringshareOaiDc):
    @classmethod
    def parse_source_file(cls, source_file: str) -> Iterator[Tag]:
        """Yield records from harvested OAI + API gathered records for possible delete."""
        yield from cls._yield_oai_xml_records_for_indexing(source_file)
        yield from cls._yield_api_records_for_deleting()

    @classmethod
    def _yield_oai_xml_records_for_indexing(cls, source_file: str) -> Iterator[Tag]:
        """Yield OAI records from extracted XML file.

        This functionality is a direct port from XMLTransformer, but allows for a custom
        self.parse_source_file in this transformer class.
        """
        with smart_open.open(source_file, "rb") as file:
            for _, element in etree.iterparse(
                file,
                tag="{*}record",
                encoding="utf-8",
                recover=True,
            ):
                record_string = etree.tostring(element, encoding="utf-8")
                record = cls.parse_bs4_in_isolated_thread(record_string)
                yield record
                element.clear()

    @classmethod
    def _yield_api_records_for_deleting(cls) -> Iterator[Tag]:
        """Yield synthetic OAI records that will prompt deletes in TIMDEX.

        This method will yield stubbed OAI records *as-if* the Springshare OAI endpoint
        produced deletes.  This is achieved by querying the Springshare API, retrieving
        a list of public/non-hidden AZ items, and comparing to a managed list of last
        known public/non-hidden AZ items.  Any items that are no longer public should
        be removed from TIMDEX, which these synthetic OAI XML records archive.
        """
        if LAST_AZ_IDENTIFIERS_PATH is None:
            raise RuntimeError(
                "Env var 'LAST_AZ_IDENTIFIERS_PATH' must be set "
                "for the 'researchdatabases' transformation'"
            )

        client = LibGuidesAPIClient()

        # retrieve current AZ identifiers from API
        az_current_identifiers = client.get_current_az_identifiers()

        # retrieve previous AZ identifiers from file
        with smart_open.open(LAST_AZ_IDENTIFIERS_PATH) as f:
            az_previous_identifiers = f.read().splitlines()

        # isolate identifiers from previous list not in current list
        deleted_identifiers = set(az_previous_identifiers).difference(
            az_current_identifiers
        )
        logger.info(
            f"{len(deleted_identifiers)} identifiers identified for deletion: "
            f"{list(deleted_identifiers)}"
        )

        # yield fake OAI records that mark a record for delete
        now_date = datetime.now(tz=UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
        for deleted_identifier in deleted_identifiers:
            oai_delete_record = f"""
            <record>
                <header status="deleted">
                    <identifier>oai:libguides.com:az/{deleted_identifier}</identifier>
                    <datestamp>{now_date}</datestamp>
                    <setSpec>az</setSpec>
                </header>
                <note>This is a synthetic delete record created by Transmogrifier.</note>
                <metadata />
            </record>
            """
            yield BeautifulSoup(oai_delete_record, "xml")

        # update AZ identifiers list with current AZ items
        with smart_open.open(LAST_AZ_IDENTIFIERS_PATH, "w") as f:
            f.writelines(f"{identifier}\n" for identifier in az_current_identifiers)
