"""Transformer module."""

from __future__ import annotations

import json
import logging
import os
from abc import ABC, abstractmethod
from importlib import import_module
from typing import TYPE_CHECKING, TypeAlias, final

import smart_open  # type: ignore[import-untyped]
from attrs import asdict

# Note: the lxml module in defusedxml is deprecated, so we have to use the
# regular lxml library. Transmogrifier only parses data from known sources so this
# should not be a security issue.
import transmogrifier.models as timdex
from transmogrifier.config import SOURCES
from transmogrifier.helpers import DeletedRecordEvent, generate_citation

if TYPE_CHECKING:
    from collections.abc import Iterator

    from bs4 import Tag  # type: ignore[import-untyped]

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
    def __iter__(self) -> Iterator[timdex.TimdexRecord]:
        """Iterate over transformed records."""
        return self

    @final
    def __next__(self) -> timdex.TimdexRecord:
        """Return next transformed record."""
        while True:
            source_record = next(self.source_records)
            self.processed_record_count += 1
            try:
                record = self.transform(source_record)
            except DeletedRecordEvent as error:
                self.deleted_records.append(error.timdex_record_id)
                continue
            if record:
                self.transformed_record_count += 1
                return record
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
            message = "No records processed from input file, needs investigation"
            raise ValueError(message)
        if deleted_records := self.deleted_records:
            deleted_output_file = output_file.replace("index", "delete").replace(
                "json", "txt"
            )
            self._write_deleted_records_to_txt_file(deleted_records, deleted_output_file)

    @final
    def _write_timdex_records_to_json_file(self, output_file: str) -> int:
        """
        Write TIMDEX records to JSON file.

        Args:
            output_file: The JSON file used for writing TIMDEX records.
        """
        count = 0
        try:
            record: timdex.TimdexRecord = next(self)
        except StopIteration:
            return count
        with smart_open.open(output_file, "w") as file:
            file.write("[\n")
            while record:
                file.write(
                    json.dumps(
                        asdict(
                            record,
                            filter=lambda _, value: value is not None,
                        ),
                        indent=2,
                    )
                )
                count += 1
                if count % int(os.getenv("STATUS_UPDATE_INTERVAL", "1000")) == 0:
                    logger.info(
                        "Status update: %s records written to output file so far!",
                        count,
                    )
                try:
                    record: timdex.TimdexRecord = next(self)  # type: ignore[no-redef]
                except StopIteration:
                    break
                file.write(",\n")
            file.write("\n]")
        return count

    @final
    @staticmethod
    def _write_deleted_records_to_txt_file(
        deleted_records: list[str], output_file: str
    ) -> None:
        """Write deleted records to the specified text file.

        Args:
            deleted_records: The deleted records to write to file.
            output_file: The text file used for writing deleted records.
        """
        with smart_open.open(output_file, "w") as file:
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
        return transformer_class(source, source_records)

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

    @final
    def _transform(
        self, source_record: dict[str, JSON] | Tag
    ) -> timdex.TimdexRecord | None:
        """
        Private method called for both XML and JSON transformations, where
        all logic is shared except source_record type.

        May not be overridden.

        Args:
            source_record: A single source record.
        """
        if self.record_is_deleted(source_record):
            source_record_id = self.get_source_record_id(source_record)
            timdex_record_id = self.get_timdex_record_id(
                self.source, source_record_id, source_record
            )
            raise DeletedRecordEvent(timdex_record_id)
        optional_fields = self.get_optional_fields(source_record)
        if optional_fields is None:
            return None

        fields = {
            **self.get_required_fields(source_record),
            **optional_fields,
        }

        fields = self.create_dates_and_locations_from_publishers(fields)
        fields = self.create_locations_from_spatial_subjects(fields)

        # If citation field was not present, generate citation from other fields
        if fields.get("citation") is None:
            fields["citation"] = generate_citation(fields)
        if fields.get("content_type") is None:
            fields["content_type"] = ["Not specified"]

        return timdex.TimdexRecord(**fields)

    @abstractmethod
    def transform(
        self, source_record: dict[str, JSON] | Tag
    ) -> timdex.TimdexRecord | None:
        """
        Call Transformer._transform method to transform source record to TIMDEX record.

        Must be overridden by format subclasses.

        Args:
            source_record: A single source record.
        """

    @abstractmethod
    def get_required_fields(self, source_record: dict[str, JSON] | Tag) -> dict:
        """
        Get required TIMDEX fields from a source record.

        Must be overridden by format subclasses.

        Args:
            source_record: A single source record.
        """

    @classmethod
    @abstractmethod
    def get_main_titles(cls, source_record: dict[str, JSON] | Tag) -> list[str]:
        """
        Retrieve main title(s) from an source record.

        Must be overridden by source subclasses.

        Args:
            source_record: A single source record.
        """

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

    @classmethod
    @abstractmethod
    def get_source_record_id(cls, source_record: dict[str, JSON] | Tag) -> str:
        """
        Get or generate a source record ID from a source record.

        Must be overridden by source subclasses.

        Args:
            source_record: A single source record.
        """

    @classmethod
    @abstractmethod
    def record_is_deleted(cls, source_record: dict[str, JSON] | Tag) -> bool:
        """
        Determine whether record has a status of deleted.

        Must be overridden by source subclasses.

        Args:
            source_record: A single source record.
        """

    def get_optional_fields(self, _source_record: dict[str, JSON] | Tag) -> dict | None:
        """
        Retrieve optional TIMDEX fields from a source record.

        May be overridden by source subclasses.

        Args:
            source_record: A single source record.
        """
        return {}

    @final
    @staticmethod
    def create_dates_and_locations_from_publishers(fields: dict) -> dict:
        """Add Date and Location objects based on data in publishers field.

        Args:
            fields: A dict of fields representing a TIMDEX record.
        """
        if not fields.get("publishers"):
            return fields
        for publisher in fields["publishers"]:
            if publisher.date:
                publisher_date = timdex.Date(
                    kind="Publication date", value=publisher.date
                )
                if publisher_date not in fields.setdefault("dates", []):
                    fields["dates"].append(publisher_date)
            if publisher.location:
                publisher_location = timdex.Location(
                    kind="Place of Publication", value=publisher.location
                )
                if publisher_location not in fields.setdefault("locations", []):
                    fields["locations"].append(publisher_location)
        return fields

    @final
    @staticmethod
    def create_locations_from_spatial_subjects(fields: dict) -> dict:
        """Add Location objects for spatial subjects.

        Args:
           fields: A dict of fields representing a TIMDEX record.
        """
        if fields.get("subjects") is None:
            return fields

        spatial_subjects = [
            subject
            for subject in fields.get("subjects", [])  # defaults to empty list
            if subject.kind == "Dublin Core; Spatial" and subject.value is not None
        ]

        for subject in spatial_subjects:
            for place_name in subject.value:
                subject_location = timdex.Location(value=place_name, kind="Place Name")
                if subject_location not in fields.setdefault("locations", []):
                    fields["locations"].append(subject_location)
        return fields
