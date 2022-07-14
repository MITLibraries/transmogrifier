"""Transformer module."""
import logging
from abc import ABCMeta, abstractmethod
from typing import Iterator, Optional, final

from bs4 import Tag

from transmogrifier.config import SOURCES
from transmogrifier.helpers import generate_citation
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
        self.source_base_url = SOURCES[source]["base_url"]
        self.source_name = SOURCES[source]["name"]
        self.input_records = input_records
        self.processed_record_count = 0
        self.transformed_record_count = 0
        self.skipped_record_count = 0

    def __iter__(self) -> Iterator[TimdexRecord]:
        """Iterate over transformed records."""
        return self

    def __next__(self) -> TimdexRecord:
        """Return next transformed record."""
        xml = next(self.input_records)
        self.processed_record_count += 1
        record = self.transform(xml)
        if record:
            self.transformed_record_count += 1
            return record
        else:
            self.skipped_record_count += 1
            return self.__next__()

    @abstractmethod
    def get_optional_fields(self, xml: Tag) -> dict:
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
    @abstractmethod
    def get_source_record_id(cls, xml: Tag) -> str:
        """
        Get or generate a source record ID from an XML record.

        May be overridden by source subclasses if needed.

        Args:
            xml: A BeautifulSoup Tag representing a single XML record
        """
        return ""

    @final
    def get_required_fields(self, xml: Tag) -> dict:
        """
        Get required TIMDEX fields from an XML record.

        May not be overridden.

        Args:
            xml: A BeautifulSoup Tag representing a single OAI-PMH XML record.
        """
        source_record_id = self.get_source_record_id(xml)
        title = self.get_valid_title(source_record_id, xml)
        return {
            "source": self.source_name,
            "source_link": self.source_base_url + source_record_id,
            "timdex_record_id": f"{self.source}:{source_record_id.replace('/', '-')}",
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
        if self.get_optional_fields(xml) == {"Unaccepted content_type": "skip"}:
            return None
        else:
            fields = {**self.get_required_fields(xml), **self.get_optional_fields(xml)}

            # If citation field was not present, generate citation from other fields
            if fields.get("citation") is None:
                fields["citation"] = generate_citation(fields)

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
        if all_titles and all_titles[0].string:
            title = all_titles[0].string
        else:
            logger.warning(
                "Record %s was missing a title, source record should be investigated.",
                source_record_id,
            )
            title = "Title not provided"
        return title
