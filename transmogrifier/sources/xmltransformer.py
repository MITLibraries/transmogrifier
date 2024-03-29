from __future__ import annotations

from typing import TYPE_CHECKING, final

import smart_open  # type: ignore[import-untyped]
from bs4 import BeautifulSoup, Tag  # type: ignore[import-untyped]

# Note: the lxml module in defusedxml is deprecated, so we have to use the
# regular lxml library. Transmogrifier only parses data from known sources so this
# should not be a security issue.
from lxml import etree  # nosec B410

from transmogrifier.sources.transformer import Transformer

if TYPE_CHECKING:
    from collections.abc import Iterator

    import transmogrifier.models as timdex


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
                record = BeautifulSoup(record_string, "xml")
                yield record
                element.clear()

    @final
    def transform(self, source_record: Tag) -> timdex.TimdexRecord | None:
        """
        Call Transformer._transform method to transform XML record to TIMDEX record.

        May not be overridden.

        Args:
            source_record: A BeautifulSoup Tag representing a single XML record.
        """
        return self._transform(source_record)

    @final
    def get_required_fields(self, source_record: Tag) -> dict:
        """
        Get required TIMDEX fields from an XML record.

        May not be overridden.

        Args:
            source_record: A BeautifulSoup Tag representing a single source record.
        """
        source_record_id = self.get_source_record_id(source_record)

        # run methods to generate required fields
        source_link = self.get_source_link(
            self.source_base_url, source_record_id, source_record
        )
        timdex_record_id = self.get_timdex_record_id(
            self.source, source_record_id, source_record
        )
        title = self.get_valid_title(source_record_id, source_record)

        return {
            "source": self.source_name,
            "source_link": source_link,
            "timdex_record_id": timdex_record_id,
            "title": title,
        }

    @classmethod
    def get_main_titles(cls, _source_record: Tag) -> list[Tag]:
        """
        Retrieve main title(s) from an XML record.

        May be overridden by source subclasses.

        Args:
            source_record: A BeautifulSoup Tag representing a single XML record.
        """
        return []

    @classmethod
    def get_source_link(
        cls,
        source_base_url: str,
        source_record_id: str,
        _source_record: Tag,
    ) -> str:
        """
        Class method to set the source link for the item.

        May be overridden by source subclasses if needed.

        Default behavior is to concatenate the source base URL + source record id.

        Args:
            source_base_url: Source base URL.
            source_record_id: Record identifier for the source record.
            source_record: A BeautifulSoup Tag representing a single XML record.
                - not used by default implementation, but could be useful for subclass
                    overrides
        """
        return source_base_url + source_record_id

    @classmethod
    def get_timdex_record_id(
        cls, source: str, source_record_id: str, _source_record: Tag
    ) -> str:
        """
        Class method to set the TIMDEX record id.

        May be overridden by source subclasses if needed.

        Default behavior is to concatenate the source name + source record id.

        Args:
            source: Source name.
            source_record_id: Record identifier for the source record.
            source_record: A BeautifulSoup Tag representing a single XML record.
                - not used by default implementation, but could be useful for subclass
                overrides
        """
        return f"{source}:{source_record_id.replace('/', '-')}"

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
        if source_record.find("header", status="deleted"):
            return True
        return False

    def get_optional_fields(self, _source_record: Tag) -> dict | None:
        """
        Retrieve optional TIMDEX fields from an XML record.

        May be overridden by source subclasses.

        Args:
            source_record: A BeautifulSoup Tag representing a single XML record
        """
        return {}
