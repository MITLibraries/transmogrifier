from __future__ import annotations

from typing import TYPE_CHECKING, final

import smart_open  # type: ignore[import-untyped]
from bs4 import BeautifulSoup, Tag  # type: ignore[import-untyped]

# Note: the lxml module in defusedxml is deprecated, so we have to use the
# regular lxml library. Transmogrifier only parses data from known sources so this
# should not be a security issue.
from lxml import etree  # nosec B410

from transmogrifier.helpers import dedupe_list_of_values
from transmogrifier.sources.transformer import Transformer

if TYPE_CHECKING:
    from collections.abc import Iterator

    import transmogrifier.models as timdex


class XMLTransformer(Transformer):
    """XML transformer class."""

    nsmap: dict

    @final
    @classmethod
    def parse_source_file(cls, source_file: str) -> Iterator[etree._Element]:
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
                yield element
                element.clear()

    @final
    @classmethod
    def xpath_query(cls, element: etree._Element, xpath_expr: str):
        return element.xpath(xpath_expr, namespaces=cls.nsmap)

    @final
    @staticmethod
    def remove_whitespace(string: str | None) -> str | None:
        """Removes newlines and excessive whitespace from a string."""
        if string is None:
            return None
        cleaned = " ".join(string.split())
        return cleaned if cleaned else None

    @final
    @classmethod
    def single_string_from_xpath(
        cls, element: etree._Element, xpath_expr: str
    ) -> str | None:
        """Return single string or None from an Xpath query.

        If the XPath query returns MORE than one textual element, an exception will be
        raised.
        """
        matches = cls.xpath_query(element, xpath_expr)
        if not matches:
            return None
        if len(matches) > 1:
            message = (
                "Expected one or none matches for XPath query, "
                f"but {len(matches)} were found."
            )
            raise ValueError(message)
        return cls.remove_whitespace(matches[0].text)

    @final
    @classmethod
    def string_list_from_xpath(cls, element: etree._Element, xpath_expr: str) -> list:
        """Return unique list of strings from XPath matches.

        A list will always be returned, though empty strings and None values will be
        filtered out. Order will be order discovered via XPath.
        """
        matches = cls.xpath_query(element, xpath_expr)
        strings = [cls.remove_whitespace(match.text) for match in matches]
        strings = [string for string in strings if string]
        if all(string is None or string == "" for string in strings):
            return []
        return dedupe_list_of_values(strings)

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
