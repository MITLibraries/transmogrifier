import logging
from collections.abc import Iterator
from datetime import UTC, datetime

import smart_open  # type: ignore[import-untyped]
from bs4 import BeautifulSoup, Tag
from lxml import etree
from timdex_dataset_api import TIMDEXDataset  # type: ignore[import-untyped]

from transmogrifier import config
from transmogrifier.exceptions import CriticalError
from transmogrifier.helpers import LibGuidesAPIClient
from transmogrifier.sources.xml.springshare import SpringshareOaiDc

logger = logging.getLogger(__name__)

# percentage of total records that if marked for deletion, indicate a problem
DELETION_COUNT_THRESHOLD = 0.8


class ResearchDatabases(SpringshareOaiDc):
    @classmethod
    def parse_source_file(cls, source_file: str) -> Iterator[Tag]:
        """Yield records from harvested OAI + API gathered records for possible delete.

        If the following env vars are not set, detecting deleted records will be skipped:
            - LIBGUIDES_API_TOKEN
            - LIBGUIDES_CLIENT_ID
            - TIMDEX_DATASET_LOCATION
        """
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
        a list of public/non-hidden AZ items, and comparing current records in the TIMDEX
        dataset.  Any items that are present in the dataset but no longer public should
        be removed from TIMDEX, which these synthetic OAI XML records achieve.
        """
        # bail early if not all required env vars are set;
        # attributes are accessed at call time so tests can monkeypatch them
        if not all(
            [
                config.LIBGUIDES_API_TOKEN,
                config.LIBGUIDES_CLIENT_ID,
                config.TIMDEX_DATASET_LOCATION,
            ]
        ):
            logger.warning(
                "Skipping deleting record detection, not all required env vars are set."
            )
            return None

        client = LibGuidesAPIClient()

        # retrieve current AZ identifiers from API
        az_current_identifiers = client.get_current_az_identifiers()

        # retrieve previous AZ identifiers from current TIMDEX dataset records
        dataset_az_identifiers = cls._get_current_dataset_az_identifiers()

        # isolate identifiers from timdex dataset not in current list
        deleted_identifiers = set(dataset_az_identifiers).difference(
            az_current_identifiers
        )

        # raise an exception if the records marked for delete exceed a threshold
        if dataset_az_identifiers:
            deletion_ratio = len(deleted_identifiers) / len(dataset_az_identifiers)
            if deletion_ratio > DELETION_COUNT_THRESHOLD:
                raise CriticalError(
                    f"The number of records marked for deletion for 'researchdatabases' "
                    "exceeds the deletion percentage threshold of: "
                    f"{DELETION_COUNT_THRESHOLD}%.  This may indicate an issue with "
                    f"pulling identifiers from the Springshare API.  It is therefore "
                    f"unsafe to continue."
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

    @classmethod
    def _get_current_dataset_az_identifiers(cls) -> list[str]:
        """Fetch AZ identifiers from current records in TIMDEX dataset.

        This method retrieves the timdex_record_id of all current records, then parses
        the integer identifier suffix that matches the identifier found in Springshare
        OAI and API outputs.

        Any identifier present in the dataset, not present in Springshare OAI/API, should
        be deleted.
        """
        timdex_dataset = TIMDEXDataset(config.TIMDEX_DATASET_LOCATION)
        return list(
            timdex_dataset.conn.query(
                """
                select
                    string_split(timdex_record_id, 'az-')[2] as az_identifier
                from metadata.current_records
                where source = 'researchdatabases'
                and action='index';
                """
            )
            .to_df()
            .az_identifier
        )
