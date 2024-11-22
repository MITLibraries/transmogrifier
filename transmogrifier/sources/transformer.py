"""Transformer module."""

from __future__ import annotations

import json
import logging
import os
import re
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass
from importlib import import_module
from typing import TYPE_CHECKING, final

import pyarrow as pa
import pyarrow.dataset as ds
import smart_open  # type: ignore[import-untyped]
from attrs import asdict
from bs4 import Tag  # type: ignore[import-untyped]

import transmogrifier.models as timdex
from transmogrifier.config import SOURCES, get_etl_version
from transmogrifier.exceptions import DeletedRecordEvent, SkippedRecordEvent
from transmogrifier.helpers import generate_citation, validate_date

if TYPE_CHECKING:
    from collections.abc import Callable, Iterator

    from transmogrifier.models import TimdexRecord

logger = logging.getLogger(__name__)

type JSON = dict[str, "JSON"] | list["JSON"] | str | int | float | bool | None

PARQUET_DATASET_BATCH_SIZE = 1_000


@dataclass
class ETLRecord:
    timdex_record_id: str | None
    serialized_source_record: bytes | None
    transformed_record: TimdexRecord | None
    action: str

    def serialized_transformed_record(self) -> bytes | None:
        """Serialize TimdexRecord to binary JSON string if set."""
        if self.transformed_record:
            return json.dumps(self.transformed_record.asdict()).encode()
        return None


class Transformer(ABC):
    """Base transformer class."""

    @final
    def __init__(
        self,
        source: str,
        source_records: Iterator[dict[str, JSON] | Tag],
        run_id: str | None = None,
    ) -> None:
        """
        Initialize Transformer instance.

        Args:
            source: Source repository label. Must match a source key from config.SOURCES.
            source_records: A set of source records to be processed.
            run_id: A unique identifier for this invocation of Transmogrifier.
        """
        self.source: str = source
        self.source_base_url: str = SOURCES[source]["base-url"]
        self.source_name = SOURCES[source]["name"]
        self.source_records: Iterator[JSON | Tag] = source_records
        self.processed_record_count: int = 0
        self.transformed_record_count: int = 0
        self.skipped_record_count: int = 0
        self.deleted_records: list[str] = []
        self.run_id: str = self.set_run_id(run_id)
        self.partition_values: dict[str, str] | None = None

    @final
    def __iter__(self) -> Iterator[timdex.TimdexRecord | ETLRecord]:
        """Iterate over transformed records."""
        return self

    @final
    def __next__(self) -> timdex.TimdexRecord | ETLRecord:
        """Return next transformed record."""
        # NOTE: FEATURE FLAG: branching logic will be removed after v2 work is complete
        etl_version = get_etl_version()
        match etl_version:
            case 1:
                return self._etl_v1_next_iter_method()
            case 2:
                return self._etl_v2_next_iter_method()

    # NOTE: FEATURE FLAG: branching logic + method removed after v2 work is complete
    def _etl_v1_next_iter_method(self) -> timdex.TimdexRecord:
        """Transformer.__next__ behavior for ETL version 1."""
        while True:
            source_record = next(self.source_records)
            self.processed_record_count += 1
            try:
                record = self.transform(source_record)
            except DeletedRecordEvent as error:
                self.deleted_records.append(error.timdex_record_id)
                continue
            except SkippedRecordEvent:
                self.skipped_record_count += 1
                continue
            self.transformed_record_count += 1
            return record

    # NOTE: FEATURE FLAG: method logic will move directly to __next__ definition
    def _etl_v2_next_iter_method(self) -> ETLRecord:
        """Transformer.__next__ behavior for ETL version 2."""
        while True:
            transformed_record = None
            timdex_record_id = None

            source_record = next(self.source_records)
            self.processed_record_count += 1

            try:
                transformed_record = self.transform(source_record)
                timdex_record_id = transformed_record.timdex_record_id
                self.transformed_record_count += 1
                action = "index"

            except DeletedRecordEvent as error:
                self.deleted_records.append(error.timdex_record_id)
                timdex_record_id = error.timdex_record_id
                action = "delete"

            except SkippedRecordEvent:
                self.skipped_record_count += 1
                action = "skip"

            return ETLRecord(
                timdex_record_id=timdex_record_id,
                serialized_source_record=self.serialize_source_record(source_record),
                transformed_record=transformed_record,
                action=action,
            )

    def set_run_id(self, run_id: str | None) -> str:
        """Method to set run_id for Transmogrifier run."""
        if not run_id:
            logger.info("explicit run_id not passed, minting new UUID")
            run_id = str(uuid.uuid4())
        message = f"run_id set: '{run_id}'"
        logger.info(message)
        return run_id

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
    def load(
        cls, source: str, source_file: str, run_id: str | None = None
    ) -> Transformer:
        """
        Instantiate specified transformer class and populate with source records.

        Args:
            source: Source repository label. Must match a source key from config.SOURCES.
            source_file: A file containing source records to be transformed.
            run_id: A unique identifier for this invocation of Transmogrifier.
        """
        transformer_class = cls.get_transformer(source)
        source_records = transformer_class.parse_source_file(source_file)
        transformer = transformer_class(source, source_records, run_id=run_id)

        # NOTE: FEATURE FLAG: branching logic will be removed after v2 work is complete
        etl_version = get_etl_version()
        if etl_version == 2:  # noqa: PLR2004
            transformer.set_dataset_partition_values(source_file)

        return transformer

    def set_dataset_partition_values(self, source_file: str) -> None:
        """Get dictionary of partition values required for writing to parquet dataset.

        This method is called prior to writing the transformed records to the parquet
        dataset, providing values needed for appropriate partitioning.  Not all values
        parsed are used.

        Example output:
            {
                'source': 'alma',
                'run_date': '2023-01-13',
                'run_type': 'full',
                'stage': 'extracted',
                'action': 'index',
                'index': '01',
                'file_type': 'xml',
                'run_id': '1bdd7b0e-0155-43ad-bd62-3ee305d6fa4b'
            }
        """
        filename = source_file.split("/")[-1]

        match_result = re.match(
            r"^([\w\-]+?)-(\d{4}-\d{2}-\d{2})-(\w+)-(\w+)-records-to-(.+?)(?:_(\d+))?\.(\w+)$",
            filename,
        )
        if not match_result:
            message = f"Provided S3 URI and filename is invalid: {filename}."
            raise ValueError(message)

        keys = ["source", "run_date", "run_type", "stage", "action", "index", "file_type"]
        try:
            partition_values = dict(zip(keys, match_result.groups(), strict=True))
        except ValueError as exception:
            message = f"Provided S3 URI and filename is invalid: {filename}."
            raise ValueError(message) from exception

        partition_values.update({"run_id": self.run_id})

        self.partition_values = partition_values

    def serialize_source_record(self, source_record: Tag | dict) -> bytes | None:
        if isinstance(source_record, Tag):
            return source_record.encode()
        if isinstance(source_record, dict):
            return json.dumps(source_record).encode()
        return None

    @final
    def transform(self, source_record: dict[str, JSON] | Tag) -> timdex.TimdexRecord:
        """
        Transform source record into TimdexRecord instance.

        Instantiates a TimdexRecord instance with required fields and runs fields methods
        for optional fields. The optional field methods return values or exceptions that
        prompt the __next__ method to skip the entire record.

        After optional fields are set, derived fields are generated from the required
        optional field values set by the source transformer.

        May not be overridden.

        Args:
            source_record: A single source record.
        """
        if self.record_is_deleted(source_record):
            timdex_record_id = self.get_timdex_record_id(source_record)
            raise DeletedRecordEvent(timdex_record_id)

        timdex_record = timdex.TimdexRecord(
            source=self.source_name,
            source_link=self.get_source_link(source_record),
            timdex_record_id=self.get_timdex_record_id(source_record),
            title=self.get_valid_title(source_record),
        )

        for field_name, field_method in self.get_optional_field_methods():
            setattr(timdex_record, field_name, field_method(source_record))

        self.generate_derived_fields(timdex_record)

        return timdex_record

    # NOTE: FEATURE FLAG: method will be removed after v2 work is complete
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

    # NOTE: FEATURE FLAG: method will be removed after v2 work is complete
    @final
    def _write_timdex_records_to_json_file(self, output_file: str) -> int:
        """
        Write TIMDEX records to JSON file.

        Args:
            output_file: The JSON file used for writing TIMDEX records.
        """
        count = 0
        try:
            record: timdex.TimdexRecord = next(self)  # type: ignore[assignment]
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

    # NOTE: FEATURE FLAG: method will be removed after v2 work is complete
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

    def write_to_parquet_dataset(self, dataset_location: str) -> list[str]:
        """Write batches of ETLRecords to parquet dataset.

        And ETLRecord contains both the original source record, the new transformed
        record, and some metadata about the input file.

        NOTE: this method is a WIP.  While functional, and demonstrative of v1 / v2
        branching, it's possible we will roll up dataset reading and writing into a
        standalone, installable python library.
        """
        schema = pa.schema(
            (
                pa.field("timdex_record_id", pa.string()),
                pa.field("source_record", pa.binary()),
                pa.field("transformed_record", pa.binary()),
                pa.field("source", pa.string()),
                pa.field("run_date", pa.date32()),
                pa.field("run_type", pa.string()),
                pa.field("run_id", pa.string()),
                pa.field("action", pa.string()),
            )
        )
        partition_columns = ["source", "run_date", "run_type", "action", "run_id"]

        written_files = []
        ds.write_dataset(
            self.yield_record_rows_for_writing(),
            schema=schema,
            base_dir=dataset_location,
            partitioning=partition_columns,
            partitioning_flavor="hive",
            format="parquet",
            basename_template="records-{i}.parquet",
            existing_data_behavior="delete_matching",
            use_threads=True,
            max_rows_per_group=PARQUET_DATASET_BATCH_SIZE,
            max_rows_per_file=100_000,
            file_visitor=lambda written_file: written_files.append(written_file),
        )
        return written_files

    def yield_record_rows_for_writing(
        self, batch_size: int = PARQUET_DATASET_BATCH_SIZE
    ) -> Iterator:
        """Prepare batches of transformed records for writing.

        Each row in the batch includes a serialized form of the original source record,
        the transformed TIMDEX record, and metadata from the input file used for
        partitioning during write.

        NOTE: this method is a WIP.  While functional, and demonstrative of v1 / v2
        branching, it will likely undergo revisions and still needs testing.
        """
        records = []
        for etl_record in self:

            if not isinstance(etl_record, ETLRecord):
                message = "ETLRecord instance required for batch creation"
                raise TypeError(message)
            if not isinstance(self.partition_values, dict):
                message = "Transformer.partition_values is not a dictionary"
                raise TypeError(message)

            record = {
                "timdex_record_id": etl_record.timdex_record_id,
                "source_record": etl_record.serialized_source_record,
                "transformed_record": etl_record.serialized_transformed_record(),
                "source": self.partition_values["source"],
                "run_date": self.partition_values["run_date"],
                "run_type": self.partition_values["run_type"],
                "run_id": self.run_id,
                "action": etl_record.action,
            }
            records.append(record)

            if len(records) >= batch_size:
                batch = pa.RecordBatch.from_pylist(records)
                yield batch
                records = []

        if records:
            batch = pa.RecordBatch.from_pylist(records)
            yield batch

    @final
    def get_valid_title(self, source_record: dict[str, JSON] | Tag) -> str:
        """
        Retrieves main title(s) from a source record and returns a valid title string.

        May not be overridden.

        If the list of main titles retrieved from the source record is empty or the
        title element has no string value, inserts standard language to represent a
        missing title field.

        Args:
            source_record: A single source record.
        """
        all_titles = self.get_main_titles(source_record)
        title_count = len(all_titles)
        if title_count > 1:
            logger.warning(
                "Record %s has multiple titles. Using the first title from the "
                "following titles found: %s",
                self.get_source_record_id(source_record),
                all_titles,
            )
        if title_count >= 1:
            title = all_titles[0]
        else:
            logger.warning(
                "Record %s was missing a title, source record should be investigated.",
                self.get_source_record_id(source_record),
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

    @classmethod
    @abstractmethod
    def get_main_titles(cls, source_record: dict[str, JSON] | Tag) -> list[str]:
        """
        Retrieve main title(s) from an source record.

        Must be overridden by source subclasses.

        Args:
            source_record: A single source record.
        """

    @abstractmethod
    def get_source_link(
        self,
        source_record: dict[str, JSON] | Tag,
    ) -> str:
        """
        Class method to set the source link for the item.

        Must be overridden by source subclasses.

        Args:
            source_record: A single source record.
        """

    @abstractmethod
    def get_timdex_record_id(self, source_record: dict[str, JSON] | Tag) -> str:
        """
        Class method to set the TIMDEX record id.

        Must be overridden by source subclasses.

        Args:
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

    @final
    def get_optional_field_methods(self) -> Iterator[tuple[str, Callable]]:
        """
        Return optional TIMDEX field names and corresponding methods.

        May not be overridden.
        """
        for field_name in timdex.TimdexRecord.get_optional_field_names():
            if field_method := getattr(self, f"get_{field_name}", None):
                yield field_name, field_method

    @final
    def generate_derived_fields(
        self, timdex_record: timdex.TimdexRecord
    ) -> timdex.TimdexRecord:
        """
        Generate field values based on existing values in TIMDEX record.

        This method sets or extends the following fields:
            - dates: list[Date]
            - locations: list[Location]
            - citation: str
            - content_type: str

        May not be overridden.
        """
        # dates
        derived_dates = timdex_record.dates or []
        derived_dates.extend(self.create_dates_from_publishers(timdex_record))
        timdex_record.dates = derived_dates or None

        # locations
        derived_locations = timdex_record.locations or []
        derived_locations.extend(self.create_locations_from_publishers(timdex_record))
        derived_locations.extend(
            self.create_locations_from_spatial_subjects(timdex_record)
        )
        timdex_record.locations = derived_locations or None

        # citation
        timdex_record.citation = timdex_record.citation or generate_citation(
            timdex_record
        )

        # content type
        timdex_record.content_type = timdex_record.content_type or ["Not specified"]

        return timdex_record

    @final
    @staticmethod
    def create_dates_from_publishers(
        timdex_record: timdex.TimdexRecord,
    ) -> Iterator[timdex.Date]:
        """Derive Date objects based on data in publishers field.

        Args:
            timdex_record: A TimdexRecord class instance.
        """
        if timdex_record.publishers:
            for publisher in timdex_record.publishers:
                if publisher.date and validate_date(
                    publisher.date, timdex_record.timdex_record_id
                ):
                    yield timdex.Date(kind="Publication date", value=publisher.date)

    @final
    @staticmethod
    def create_locations_from_publishers(
        timdex_record: timdex.TimdexRecord,
    ) -> Iterator[timdex.Location]:
        """Derive Location objects based on data in publishers field.

        Args:
            timdex_record: A TimdexRecord class instance.
        """
        if timdex_record.publishers:
            for publisher in timdex_record.publishers:
                if publisher.location:
                    yield timdex.Location(
                        kind="Place of Publication", value=publisher.location
                    )

    @final
    @staticmethod
    def create_locations_from_spatial_subjects(
        timdex_record: timdex.TimdexRecord,
    ) -> Iterator[timdex.Location]:
        """Derive Location objects from a TimdexRecord's spatial subjects.

        Args:
           timdex_record: A TimdexRecord class instance.
        """
        if timdex_record.subjects:
            spatial_subjects = [
                subject
                for subject in timdex_record.subjects
                if subject.kind == "Dublin Core; Spatial" and subject.value is not None
            ]

            for subject in spatial_subjects:
                for place_name in subject.value:
                    yield timdex.Location(value=place_name, kind="Place Name")
