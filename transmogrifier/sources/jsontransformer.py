from __future__ import annotations

from abc import abstractmethod
from typing import TYPE_CHECKING, final

import jsonlines
import smart_open  # type: ignore[import-untyped]

from transmogrifier.sources.transformer import JSON, Transformer

if TYPE_CHECKING:
    from collections.abc import Iterator


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

    @classmethod
    @abstractmethod
    def get_main_titles(cls, source_record: dict[str, JSON]) -> list[str]:
        """
        Retrieve main title(s) from a JSON record.

        Must be overridden by source subclasses.

        Args:
            source_record: A JSON object representing a source record.
        """

    def get_source_link(self, source_record: dict[str, JSON]) -> str:
        """
        Class method to set the source link for the item.

        May be overridden by source subclasses if needed.

        Default behavior is to concatenate the source base URL + source record id.

        Args:
            source_record: A JSON object representing a source record.
        """
        return self.source_base_url + self.get_source_record_id(source_record)

    def get_timdex_record_id(
        self,
        source_record: dict[str, JSON],
    ) -> str:
        """
        Class method to set the TIMDEX record id.

        May be overridden by source subclasses if needed.

        Default behavior is to concatenate the source name + source record id.

        Args:
            source_record: A JSON object representing a source record.
        """
        return (
            f"{self.source}:{self.get_source_record_id(source_record).replace('/', '-')}"
        )

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
