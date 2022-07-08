"""Transformer module."""
from typing import Iterator

from bs4 import Tag

from transmogrifier.config import SOURCES
from transmogrifier.models import TimdexRecord


class Transformer:
    """Base transformer class."""

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

    def __iter__(self) -> Iterator[TimdexRecord]:
        """Iterate over transformed records."""
        return self

    def __next__(self) -> TimdexRecord:
        """Return next transformed record."""
        xml = next(self.input_records)
        record = self.transform(xml)
        return record

    def transform(self, xml: Tag) -> Tag:
        """
        Transform an XML record.

        Note: Base Transformer.transform() simply returns the passed XML record. Must be
        overridden by all subclasses with appropriate transform for the subclass schema.

        Args:
            xml: A BeautifulSoup Tag representing a single XML record.
        """
        return xml
