"""Transformer module."""
import logging
from abc import ABCMeta, abstractmethod
from typing import Iterator, Optional, final

from bs4 import Tag

from transmogrifier.config import SOURCES
from transmogrifier.helpers import DeletedRecord, generate_citation
from transmogrifier.models import TimdexRecord

logger = logging.getLogger(__name__)


class Transformer(object):
    """Base transformer class."""

    __metaclass__ = ABCMeta

    def __init__(self, source: str, input_records: Iterator[Tag]) -> None:
        """
        Initialize Transformer instance.

        Args:
            source: Source repository short label. Must match a source key from
                config.SOURCES
        """
        self.source = source
        self.source_base_url = SOURCES[source]["base-url"]
        self.source_name = SOURCES[source]["name"]
        self.input_records = input_records
        self.processed_record_count = 0
        self.transformed_record_count = 0
        self.skipped_record_count = 0
        self.deleted_records: list[str] = []

    def __iter__(self) -> Iterator[TimdexRecord]:
        """Iterate over transformed records."""
        return self

    def __next__(self) -> TimdexRecord:
        """Return next transformed record."""
        while True:
            xml = next(self.input_records)
            self.processed_record_count += 1
            try:
                record = self.transform(xml)
            except DeletedRecord as error:
                self.deleted_records.append(error.timdex_record_id)
                continue
            if record:
                self.transformed_record_count += 1
                return record
            else:
                self.skipped_record_count += 1
                continue

    @abstractmethod
    def get_optional_fields(self, xml: Tag) -> Optional[dict]:
        """
        Retrieve optional TIMDEX fields from an XML record.

        Must be overridden by source subclasses.

        Args:
            xml: A BeautifulSoup Tag representing a single XML record
        """
        return {}

    @classmethod
    @abstractmethod
    def get_main_titles(cls, xml: Tag) -> list[Tag]:
        """
        Retrieve main title(s) from an XML record.

        Must be overridden by source subclasses.

        Args:
            xml: A BeautifulSoup Tag representing a single XML record
        """
        return []

    @classmethod
    def get_source_record_id(cls, xml: Tag) -> str:
        """
        Get or generate a source record ID from an XML record.

        May be overridden by source subclasses if needed.

        Args:
            xml: A BeautifulSoup Tag representing a single XML record
        """
        return str(xml.header.find("identifier").string)

    @classmethod
    def record_is_deleted(cls, xml: Tag) -> bool:
        """
        Determine whether record has a status of deleted.

        May be overridden by source subclasses if needed.

        Args:
            xml: A BeautifulSoup Tag representing a single XML record
        """
        if xml.find("header", status="deleted"):
            return True
        return False

    @final
    def get_required_fields(self, xml: Tag) -> dict:
        """
        Get required TIMDEX fields from an XML record.

        May not be overridden.

        Args:
            xml: A BeautifulSoup Tag representing a single OAI-PMH XML record.
        """
        source_record_id = self.get_source_record_id(xml)

        # run methods to generate required fields
        source_link = self.get_source_link(self.source_base_url, source_record_id, xml)
        timdex_record_id = self.get_timdex_record_id(self.source, source_record_id, xml)
        title = self.get_valid_title(source_record_id, xml)

        return {
            "source": self.source_name,
            "source_link": source_link,
            "timdex_record_id": timdex_record_id,
            "title": title,
        }

    @final
    def transform(self, xml: Tag) -> Optional[TimdexRecord]:
        """
        Transform an OAI-PMH XML record into a TIMDEX record.

        May not be overridden.

        Args:
            xml: A BeautifulSoup Tag representing a single OAI-PMH XML record.
        """
        if self.record_is_deleted(xml):
            source_record_id = self.get_source_record_id(xml)
            timdex_record_id = f"{self.source}:{source_record_id.replace('/', '-')}"
            raise DeletedRecord(timdex_record_id)
        optional_fields = self.get_optional_fields(xml)
        if optional_fields is None:
            return None
        else:
            fields = {
                **self.get_required_fields(xml),
                **optional_fields,
            }

            # If citation field was not present, generate citation from other fields
            if fields.get("citation") is None:
                fields["citation"] = generate_citation(fields)
            if fields.get("content_type") is None:
                fields["content_type"] = ["Not specified"]

            return TimdexRecord(**fields)

    @final
    @classmethod
    def get_valid_title(cls, source_record_id: str, xml: Tag) -> str:
        """
        Retrieves main title(s) from an XML record and returns a valid title string.

        May not be overridden.

        If the list of main titles retrieved from the source record is empty or the
        title element has no string value, inserts standard language to represent a
        missing title field.

        Args:
            source_record_id: Record identifier for the source record.
            xml: A BeautifulSoup Tag representing a single XML record.
        """
        all_titles = cls.get_main_titles(xml)
        if len(all_titles) > 1:
            logger.warning(
                "Record %s has multiple titles. Using the first title from the "
                "following titles found: %s",
                source_record_id,
                all_titles,
            )
        if all_titles and isinstance(all_titles[0], str):
            title = all_titles[0]
        elif all_titles and all_titles[0].string:
            title = all_titles[0].string
        else:
            logger.warning(
                "Record %s was missing a title, source record should be investigated.",
                source_record_id,
            )
            title = "Title not provided"
        return title

    @classmethod
    def get_source_link(
        cls, source_base_url: str, source_record_id: str, xml: Tag
    ) -> str:
        """
        Class method to set the source link for the item.

        May be overridden by source subclasses if needed.

        Default behavior is to concatenate the source base URL + source record id.

        Args:
            source_base_url: Source base URL.
            source_record_id: Record identifier for the source record.
            xml: A BeautifulSoup Tag representing a single XML record.
                - not used by default implementation, but could be useful for subclass
                    overrides
        """
        return source_base_url + source_record_id

    @classmethod
    def get_timdex_record_id(cls, source: str, source_record_id: str, xml: Tag) -> str:
        """
        Class method to set the TIMDEX record id.

        May be overridden by source subclasses if needed.

        Default behavior is to concatenate the source name + source record id.

        Args:
            source: Source name.
            source_record_id: Record identifier for the source record.
            xml: A BeautifulSoup Tag representing a single XML record.
                - not used by default implementation, but could be useful for subclass
                overrides
        """
        return f"{source}:{source_record_id.replace('/', '-')}"
