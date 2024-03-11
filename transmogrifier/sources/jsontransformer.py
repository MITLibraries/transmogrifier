from __future__ import annotations

from abc import abstractmethod
from typing import TYPE_CHECKING, final

import jsonlines
import smart_open  # type: ignore[import-untyped]

from transmogrifier.sources.transformer import JSON, Transformer

if TYPE_CHECKING:
    from collections.abc import Iterator

    import transmogrifier.models as timdex


class JSONTransformer(Transformer):
    """JSON transformer class."""

    @final
    @classmethod
    def parse_source_file(cls, source_file: str) -> Iterator[dict[str, JSON]]:
        """
        Parse JSON file and return source records as JSON objects via an iterator.

        May not be overridden.

        Validates that records in the file are dicts for proper processing.

        Args:
            source_file: A file containing source records to be transformed.
        """
        with jsonlines.Reader(smart_open.open(source_file, "r")) as records:
            yield from records.iter(type=dict)

    @final
    def transform(self, source_record: dict[str, JSON]) -> timdex.TimdexRecord | None:
        """
        Call Transformer._transform method to transform JSON record to TIMDEX record.

        May not be overridden.

        Args:
            source_record: A JSON object representing a source record.
        """
        return self._transform(source_record)

    @final
    def get_required_fields(self, source_record: dict[str, JSON]) -> dict:
        """
        Get required TIMDEX fields from an JSON record.

        May not be overridden.

        Args:
            source_record: A JSON object representing a source record.
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
    @abstractmethod
    def get_main_titles(cls, source_record: dict[str, JSON]) -> list[str]:
        """
        Retrieve main title(s) from a JSON record.

        Must be overridden by source subclasses.

        Args:
            source_record: A JSON object representing a source record.
        """

    @classmethod
    def get_source_link(
        cls,
        source_base_url: str,
        source_record_id: str,
        _source_record: dict[str, JSON],
    ) -> str:
        """
        Class method to set the source link for the item.

        May be overridden by source subclasses if needed.

        Default behavior is to concatenate the source base URL + source record id.

        Args:
            source_base_url: Source base URL.
            source_record_id: Record identifier for the source record.
            source_record: A JSON object representing a source record.
                - not used by default implementation, but could be useful for subclass
                    overrides
        """
        return source_base_url + source_record_id

    @classmethod
    def get_timdex_record_id(
        cls,
        source: str,
        source_record_id: str,
        _source_record: dict[str, JSON],
    ) -> str:
        """
        Class method to set the TIMDEX record id.

        May be overridden by source subclasses if needed.

        Default behavior is to concatenate the source name + source record id.

        Args:
            source: Source name.
            source_record_id: Record identifier for the source record.
            source_record: A JSON object representing a source record.
                - not used by default implementation, but could be useful for subclass
                overrides
        """
        return f"{source}:{source_record_id.replace('/', '-')}"

    @classmethod
    @abstractmethod
    def get_source_record_id(cls, source_record: dict[str, JSON]) -> str:
        """
        Get or generate a source record ID from a JSON record.

        May be overridden by source subclasses if needed.

        Args:
            source_record: A JSON object representing a source record.
        """

    @classmethod
    @abstractmethod
    def record_is_deleted(cls, source_record: dict[str, JSON]) -> bool:
        """
        Determine whether record has a status of deleted.

        May be overridden by source subclasses if needed.

        Args:
            source_record: A JSON object representing a source record.
        """

    def get_optional_fields(self, _source_record: dict[str, JSON]) -> dict | None:
        """
        Retrieve optional TIMDEX fields from a JSON record.

        May be overridden by source subclasses.

        Args:
            source_record: A JSON object representing a source record.
        """
        return {}
