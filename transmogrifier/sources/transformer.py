"""Transformer module."""
from __future__ import annotations

import json
import logging
import os
from abc import ABC, abstractmethod
from importlib import import_module
from typing import Iterator, Optional, TypeAlias, final

import jsonlines
from attrs import asdict
from bs4 import BeautifulSoup, Tag

# Note: the lxml module in defusedxml is deprecated, so we have to use the
# regular lxml library. Transmogrifier only parses data from known sources so this
# should not be a security issue.
from lxml import etree  # nosec B410

from transmogrifier.config import SOURCES
from transmogrifier.helpers import DeletedRecord, generate_citation
from transmogrifier.models import TimdexRecord

logger = logging.getLogger(__name__)

JSON: TypeAlias = dict[str, "JSON"] | list["JSON"] | str | int | float | bool | None


class Transformer(ABC):
    """Base transformer class."""

    @final
    def __init__(
        self, source: str, source_records: Iterator[dict[str, JSON] | Tag]
    ) -> None:
        """
        Initialize Transformer instance.

        Args:
            source: Source repository label. Must match a source key from config.SOURCES.
            source_records: A set of source records to be processed.
        """
        self.source: str = source
        self.source_base_url: str = SOURCES[source]["base-url"]
        self.source_name = SOURCES[source]["name"]
        self.source_records: Iterator[JSON | Tag] = source_records
        self.processed_record_count: int = 0
        self.transformed_record_count: int = 0
        self.skipped_record_count: int = 0
        self.deleted_records: list[str] = []

    @final
    def __iter__(self) -> Iterator[TimdexRecord]:
        """Iterate over transformed records."""
        return self

    @final
    def __next__(self) -> TimdexRecord:
        """Return next transformed record."""
        while True:
            source_record = next(self.source_records)
            self.processed_record_count += 1
            try:
                record = self.transform(source_record)
            except DeletedRecord as error:
                self.deleted_records.append(error.timdex_record_id)
                continue
            if record:
                self.transformed_record_count += 1
                return record
            else:
                self.skipped_record_count += 1
                continue

    @final
    def transform_and_write_output_files(self, output_file: str) -> None:
        """Iterates through source records to transform and write to output files.

        Args:
            output_file: The name of the output files.
        """
        self._write_timdex_records_to_json_file(output_file)
        if self.processed_record_count == 0:
            raise ValueError(
                "No records processed from input file, needs investigation"
            )
        if deleted_records := self.deleted_records:
            deleted_output_file = output_file.replace("index", "delete").replace(
                "json", "txt"
            )
            self._write_deleted_records_to_txt_file(
                deleted_records, deleted_output_file
            )

    @final
    def _write_timdex_records_to_json_file(self, output_file: str) -> int:
        """
        Write TIMDEX records to JSON file.

        Args:
            output_file: The JSON file used for writing TIMDEX records.
        """
        count = 0
        try:
            record: TimdexRecord = next(self)
        except StopIteration:
            return count
        with open(output_file, "w") as file:
            file.write("[\n")
            while record:
                file.write(
                    json.dumps(
                        asdict(record, filter=lambda attr, value: value is not None),
                        indent=2,
                    )
                )
                count += 1
                if count % int(os.getenv("STATUS_UPDATE_INTERVAL", 1000)) == 0:
                    logger.info(
                        "Status update: %s records written to output file so far!",
                        count,
                    )
                try:
                    record: TimdexRecord = next(self)  # type: ignore[no-redef]  # noqa: E501
                except StopIteration:
                    break
                file.write(",\n")
            file.write("\n]")
        return count

    @final
    @staticmethod
    def _write_deleted_records_to_txt_file(
        deleted_records: list[str], output_file: str
    ):
        """Write deleted records to the specified text file.

        Args:
            deleted_records: The deleted records to write to file.
            output_file: The text file used for writing deleted records.
        """
        with open(output_file, "w") as file:
            for record_id in deleted_records:
                file.write(f"{record_id}\n")

    @final
    @classmethod
    def load(cls, source: str, source_file: str) -> Transformer:
        """
        Instantiate specified transformer class and populate with source records.

        Args:
            source: Source repository label. Must match a source key from config.SOURCES.
            source_file: A file containing source records to be transformed.
        """
        transformer_class = cls.get_transformer(source)
        source_records = transformer_class.parse_source_file(source_file)
        transformer = transformer_class(source, source_records)
        return transformer

    @final
    @classmethod
    def get_transformer(cls, source: str) -> type[Transformer]:
        """
        Return configured transformer class for a source.

        Source must be configured with a valid transform class path.

        Args:
            source: Source repository label. Must match a source key from config.SOURCES.

        """
        module_name, class_name = SOURCES[source]["transform-class"].rsplit(".", 1)
        source_module = import_module(module_name)
        return getattr(source_module, class_name)

    @final
    @classmethod
    def get_valid_title(
        cls, source_record_id: str, source_record: dict[str, JSON] | Tag
    ) -> str:
        """
        Retrieves main title(s) from a source record and returns a valid title string.

        May not be overridden.

        If the list of main titles retrieved from the source record is empty or the
        title element has no string value, inserts standard language to represent a
        missing title field.

        Args:
            source_record_id: Record identifier for the source record.
            source_record: A single source record.
        """
        all_titles = cls.get_main_titles(source_record)
        title_count = len(all_titles)
        if title_count > 1:
            logger.warning(
                "Record %s has multiple titles. Using the first title from the "
                "following titles found: %s",
                source_record_id,
                all_titles,
            )
        if title_count >= 1:
            title = all_titles[0]
        else:
            logger.warning(
                "Record %s was missing a title, source record should be investigated.",
                source_record_id,
            )
            title = "Title not provided"
        return title

    @classmethod
    @abstractmethod
    def parse_source_file(cls, source_file: str) -> Iterator[dict[str, JSON] | Tag]:
        """
        Parse source file and return source records via an iterator.

        Must be overridden by format subclasses.

        Args:
            source_file: A file containing source records to be transformed.
        """
        pass

    @abstractmethod
    def transform(self, source_record: dict[str, JSON] | Tag) -> Optional[TimdexRecord]:
        """
        Transform a source record into a TIMDEX record.

        Must be overridden by format subclasses.

        Args:
            source_record: A single source record.
        """
        pass

    @abstractmethod
    def get_required_fields(self, source_record: dict[str, JSON] | Tag) -> dict:
        """
        Get required TIMDEX fields from a source record.

        Must be overridden by format subclasses.

        Args:
            source_record: A single source record.
        """
        pass

    @classmethod
    @abstractmethod
    def get_main_titles(cls, source_record: dict[str, JSON] | Tag) -> list[str]:
        """
        Retrieve main title(s) from an source record.

        Must be overridden by source subclasses.

        Args:
            source_record: A single source record.
        """
        pass

    @classmethod
    @abstractmethod
    def get_source_link(
        cls,
        source_base_url: str,
        source_record_id: str,
        source_record: dict[str, JSON] | Tag,
    ) -> str:
        """
        Class method to set the source link for the item.

        Must be overridden by source subclasses.

        Args:
            source_base_url: Source base URL.
            source_record_id: Record identifier for the source record.
            source_record: A single source record.
        """
        pass

    @classmethod
    @abstractmethod
    def get_timdex_record_id(
        cls, source: str, source_record_id: str, source_record: dict[str, JSON] | Tag
    ) -> str:
        """
        Class method to set the TIMDEX record id.

        Must be overridden by source subclasses.

        Args:
            source: Source name.
            source_record_id: Record identifier for the source record.
            source_record: A single source record.
        """
        pass

    @classmethod
    @abstractmethod
    def get_source_record_id(cls, source_record: dict[str, JSON] | Tag) -> str:
        """
        Get or generate a source record ID from a source record.

        Must be overridden by source subclasses.

        Args:
            source_record: A single source record.
        """
        pass

    @classmethod
    @abstractmethod
    def record_is_deleted(cls, source_record: dict[str, JSON] | Tag) -> bool:
        """
        Determine whether record has a status of deleted.

        Must be overridden by source subclasses.

        Args:
            source_record: A single source record.
        """
        pass

    def get_optional_fields(
        self, source_record: dict[str, JSON] | Tag
    ) -> Optional[dict]:
        """
        Retrieve optional TIMDEX fields from a source record.

        May be overridden by source subclasses.

        Args:
            source_record: A single source record.
        """
        return {}


class JsonTransformer(Transformer):
    """JSON transformer class."""

    @final
    @classmethod
    def parse_source_file(cls, source_file: str) -> Iterator[dict[str, JSON]]:
        """
        Parse JSON file and return source records as JSON objects via an iterator.

        May not be overridden.

        Args:
            source_file: A file containing source records to be transformed.
        """
        with jsonlines.open(source_file) as records:
            for record in records.iter(type=dict):
                yield record

    @final
    def transform(self, source_record: dict[str, JSON]) -> Optional[TimdexRecord]:
        """
        Transform a JSON record into a TIMDEX record.

        May not be overridden.

        Args:
            source_record: A JSON object representing a source record.
        """
        if self.record_is_deleted(source_record):
            source_record_id = self.get_source_record_id(source_record)
            timdex_record_id = self.get_timdex_record_id(
                self.source, source_record_id, source_record
            )
            raise DeletedRecord(timdex_record_id)
        optional_fields = self.get_optional_fields(source_record)
        if optional_fields is None:
            return None
        else:
            fields = {
                **self.get_required_fields(source_record),
                **optional_fields,
            }

            # If citation field was not present, generate citation from other fields
            if fields.get("citation") is None:
                fields["citation"] = generate_citation(fields)
            if fields.get("content_type") is None:
                fields["content_type"] = ["Not specified"]

            return TimdexRecord(**fields)

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
        pass

    @classmethod
    def get_source_link(
        cls, source_base_url: str, source_record_id: str, source_record: dict[str, JSON]
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
        cls, source: str, source_record_id: str, source_record: dict[str, JSON]
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
        pass

    @classmethod
    @abstractmethod
    def record_is_deleted(cls, source_record: dict[str, JSON]) -> bool:
        """
        Determine whether record has a status of deleted.

        May be overridden by source subclasses if needed.

        Args:
            source_record: A JSON object representing a source record.
        """
        pass

    def get_optional_fields(self, source_record: dict[str, JSON]) -> Optional[dict]:
        """
        Retrieve optional TIMDEX fields from a JSON record.

        May be overridden by source subclasses.

        Args:
            source_record: A JSON object representing a source record.
        """
        return {}


class XmlTransformer(Transformer):
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
        with open(source_file, "rb") as file:
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
    def transform(self, source_record: Tag) -> Optional[TimdexRecord]:
        """
        Transform an XML record into a TIMDEX record.

        May not be overridden.

        Args:
            source_record: A BeautifulSoup Tag representing a single XML record.
        """
        if self.record_is_deleted(source_record):
            source_record_id = self.get_source_record_id(source_record)
            timdex_record_id = self.get_timdex_record_id(
                self.source, source_record_id, source_record
            )
            raise DeletedRecord(timdex_record_id)
        optional_fields = self.get_optional_fields(source_record)
        if optional_fields is None:
            return None
        else:
            fields = {
                **self.get_required_fields(source_record),
                **optional_fields,
            }

            # If citation field was not present, generate citation from other fields
            if fields.get("citation") is None:
                fields["citation"] = generate_citation(fields)
            if fields.get("content_type") is None:
                fields["content_type"] = ["Not specified"]

            return TimdexRecord(**fields)

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
    def get_main_titles(cls, source_record: Tag) -> list[Tag]:
        """
        Retrieve main title(s) from an XML record.

        May be overridden by source subclasses.

        Args:
            source_record: A BeautifulSoup Tag representing a single XML record.
        """
        return []

    @classmethod
    def get_source_link(
        cls, source_base_url: str, source_record_id: str, source_record: Tag
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
        cls, source: str, source_record_id: str, source_record: Tag
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

    def get_optional_fields(self, source_record: Tag) -> Optional[dict]:
        """
        Retrieve optional TIMDEX fields from an XML record.

        May be overridden by source subclasses.

        Args:
            source_record: A BeautifulSoup Tag representing a single XML record
        """
        return {}
