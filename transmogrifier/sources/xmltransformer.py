from __future__ import annotations

import threading
from typing import TYPE_CHECKING, final

import smart_open  # type: ignore[import-untyped]
from bs4 import BeautifulSoup, Tag  # type: ignore[import-untyped]
from lxml import etree

from transmogrifier.sources.transformer import Transformer

if TYPE_CHECKING:
    from collections.abc import Iterator


class XMLTransformer(Transformer):
    """XML transformer class."""

    @final
    @classmethod
    def parse_source_file(cls, source_file: str) -> Iterator[Tag]:
        """
        Parse XML file and return source records as bs4 Tags via an iterator.

        May not be overridden.

        Args:
            source_file: A file containing source records to be transformed.
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
    def parse_bs4_in_isolated_thread(cls, source_record: bytes) -> Tag:
        def parse() -> Tag:
            nonlocal source_record
            source_record = BeautifulSoup(source_record, "xml")

        thread = threading.Thread(target=parse)
        thread.start()
        thread.join()
        return source_record

    @classmethod
    def get_main_titles(cls, _source_record: Tag) -> list[Tag]:
        """
        Retrieve main title(s) from an XML record.

        May be overridden by source subclasses.

        Args:
            source_record: A BeautifulSoup Tag representing a single XML record.
        """
        return []

    def get_source_link(self, source_record: Tag) -> str:
        """
        Class method to set the source link for the item.

        May be overridden by source subclasses if needed.

        Default behavior is to concatenate the source base URL + source record id.

        Args:
            source_record: A BeautifulSoup Tag representing a single XML record.
                - not used by default implementation, but could be useful for subclass
                    overrides
        """
        return self.source_base_url + self.get_source_record_id(source_record)

    def get_timdex_record_id(self, source_record: Tag) -> str:
        """
        Class method to set the TIMDEX record id.

        May be overridden by source subclasses if needed.

        Default behavior is to concatenate the source name + source record id.

        Args:
            source_record: A BeautifulSoup Tag representing a single XML record.
                - not used by default implementation, but could be useful for subclass
                overrides
        """
        return (
            f"{self.source}:{self.get_source_record_id(source_record).replace('/', '-')}"
        )

    @classmethod
    def get_source_record_id(cls, source_record: Tag) -> str:
        """
        Get or generate a source record ID from an XML record.

        May be overridden by source subclasses if needed.

        Args:
            source_record: A BeautifulSoup Tag representing a single XML record.
        """
        return str(source_record.header.find("identifier").string)

    @classmethod
    def record_is_deleted(cls, source_record: Tag) -> bool:
        """
        Determine whether record has a status of deleted.

        May be overridden by source subclasses if needed.

        Args:
            source_record: A BeautifulSoup Tag representing a single XML record
        """
        return source_record.find("header", status="deleted") is not None
