"""Transformer module."""

# ruff: noqa: D417

from __future__ import annotations

import itertools
import json
import logging
import os
import re
import uuid
from abc import ABC, abstractmethod
from datetime import UTC, datetime
from importlib import import_module
from typing import TYPE_CHECKING, final

import pyarrow as pa
import pyarrow.compute as pc
import pyarrow.dataset as ds
import smart_open
from bs4 import Tag
from lxml import etree
from pyarrow import fs
from timdex_dataset_api import (
    DatasetRecord,
    TIMDEXDataset,
)

import transmogrifier.models as timdex
from transmogrifier.config import SOURCES
from transmogrifier.exceptions import (
    CriticalError,
    DeletedRecordEvent,
    SkippedRecordEvent,
)
from transmogrifier.helpers import (
    generate_citation,
    validate_date,
)

if TYPE_CHECKING:
    from collections.abc import Callable, Iterator

logger = logging.getLogger(__name__)

type JSON = dict[str, "JSON"] | list["JSON"] | str | int | float | bool | None

PARQUET_DATASET_BATCH_SIZE = 1_000

PARQUET_FILES_SCHEMA = pa.schema(
    [
        pa.field("timdex_record_id", pa.string()),
        pa.field("source_record", pa.binary()),
        pa.field("transformed_record", pa.string()),
        pa.field("source", pa.string()),
        pa.field("run_date", pa.date32()),
        pa.field("run_type", pa.string()),
        pa.field("action", pa.string()),
        pa.field("run_id", pa.string()),
        pa.field("run_record_offset", pa.int64()),
        pa.field("run_timestamp", pa.timestamp("us", tz="UTC")),
    ]
)
PARQUET_FILES_MAX_ROWS_PER_FILE = 100_000
PARQUET_FILES_ROW_GROUP_SIZE = 5_000
PARQUET_FILES_COMPRESSION = "zstd"

INPUT_SOURCE_ERROR_MESSAGE = (
    "Exactly one input source is required: 'source_file', 'source_dataset', "
    "or 'source_parquet'"
)


class Transformer(ABC):
    """Base transformer class."""

    def __init__(
        self,
        source: str,
        source_records: Iterator[bytes | dict[str, JSON] | Tag],
        exclusion_list_path: str | None = None,
        source_file: str | None = None,
        source_dataset: str | None = None,
        source_parquet: str | None = None,
        run_id: str | None = None,
        run_timestamp: str | None = None,
    ) -> None:
        """
        Initialize Transformer instance.

        Args:
            source: Source repository label. Must match a source key from config.SOURCES.
            exclusion_list_path: S3 or local filepath to exclusion list CSV file.
            exclsion_list: The exclusion list for this particular source.
            source_records: A set of source records to be processed, as bytes to be
                parsed during transformation, or already parsed records.
            source_file: Filepath of the input source file.
            source_dataset: Location of the TIMDEX dataset with input source records.
            source_parquet: Location of parquet file(s) with input source records.
            run_id: A unique identifier associated with this ETL run.
            run_timestamp: A timestamp associated with this ETL run.
        """
        self.source: str = source
        self.exclusion_list_path: str | None = exclusion_list_path
        self._exclusion_list: list[str] | None = None
        self.source_base_url: str = SOURCES[source]["base-url"]
        self.source_name = SOURCES[source]["name"]
        self.source_records: Iterator[bytes | dict[str, JSON] | Tag] = source_records
        self.processed_record_count: int = 0
        self.transformed_record_count: int = 0
        self.skipped_record_count: int = 0
        self.error_record_count: int = 0
        self.deleted_records: list[str] = []
        self.source_file = source_file
        self.source_dataset = source_dataset
        self.source_parquet = source_parquet

        # transformed records are yielded from this private object, by default this
        # instance; with multiple workers, the CLI replaces this with records coming
        # back from the workers
        self._transformed_records: Iterator[DatasetRecord] = self

        self.run_data = self.get_run_data(
            source=source,
            source_file=source_file,
            source_dataset=source_dataset,
            source_parquet=source_parquet,
            run_id=run_id,
            run_timestamp=run_timestamp,
        )

    @property
    def run_record_offset(self) -> int:
        return self.processed_record_count - 1

    @property
    def exclusion_list(self) -> list[str] | None:
        if self.exclusion_list_path and self._exclusion_list is None:
            self._exclusion_list = self.load_exclusion_list()
        return self._exclusion_list

    def load_exclusion_list(self) -> list[str]:
        """
        Load a CSV file from path (S3 or local filesystem) and return values as a list.

        CSV file has no headers and contains identifiers to exclude, one per line.

        Args:
            exclusion_list_path: Path to exclusion list file (s3://bucket/key or local
            path).

        Raises:
            On error loading or parsing the file, raises CriticalError which will
            terminate the run.
        """
        try:
            with smart_open.open(
                str(self.exclusion_list_path), "r"
            ) as exclusion_list_file:
                rows = exclusion_list_file.readlines()
            exclusion_list = [row.strip() for row in rows if row.strip()]
        except Exception as exc:
            raise CriticalError(f"Could not load exclusion list: {exc}") from exc

        logger.info(
            f"Loaded exclusion list from {self.exclusion_list_path} with "
            f"{len(exclusion_list)} entries"
        )
        return exclusion_list

    @final
    def __iter__(self) -> Iterator[DatasetRecord]:
        """Iterate over transformed records."""
        return self._transformed_records

    @final
    def __next__(self) -> DatasetRecord:
        """Return next transformed record."""
        while True:
            source_record = None
            transformed_record = None
            timdex_record_id = None

            record = next(self.source_records)
            self.processed_record_count += 1

            try:
                source_record = (
                    self.parse_source_record(record)
                    if isinstance(record, bytes)
                    else record
                )
                transformed_record = self.transform(source_record)
                timdex_record_id = transformed_record.timdex_record_id
                transformed_record.timdex_provenance = timdex.TimdexProvenance(
                    source=self.run_data["source"],
                    run_date=self.run_data["run_date"],
                    run_id=self.run_data["run_id"],
                    run_record_offset=self.run_record_offset,
                )
                self.transformed_record_count += 1
                action = "index"

            except DeletedRecordEvent as error:
                self.deleted_records.append(error.timdex_record_id)
                timdex_record_id = error.timdex_record_id
                action = "delete"

            except SkippedRecordEvent:
                self.skipped_record_count += 1
                action = "skip"

            except CriticalError:
                raise

            except Exception as exception:
                self.error_record_count += 1
                message = f"Unhandled exception during record transformation: {exception}"
                logger.exception(message)
                action = "error"

            return DatasetRecord(
                timdex_record_id=timdex_record_id,
                source_record=(
                    record
                    if isinstance(record, bytes)
                    else self.serialize_source_record(record)
                ),
                transformed_record=(
                    json.dumps(transformed_record.asdict()).encode()
                    if transformed_record
                    else None
                ),
                action=action,
                run_record_offset=self.run_record_offset,
                **self.run_data,
            )

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
        cls,
        source: str,
        source_file: str | None = None,
        source_dataset: str | None = None,
        source_parquet: str | None = None,
        exclusion_list_path: str | None = None,
        run_id: str | None = None,
        run_timestamp: str | None = None,
    ) -> Transformer:
        """
        Instantiate specified transformer class and populate with source records.

        Args:
            source: Source repository label. Must match a source key from config.SOURCES.
            source_file: A file containing source records to be transformed.
            source_dataset: TIMDEX dataset with source records to be transformed.
            source_parquet: Parquet file(s) with source records to be transformed.
            exclusion_list_path: CSV filepath to use for explicitly skipping records.
            run_id: A unique identifier associated with this ETL run.
            run_timestamp: A timestamp associated with this ETL run.
        """
        transformer_class = cls.get_transformer(source)

        if len([i for i in (source_file, source_dataset, source_parquet) if i]) != 1:
            raise ValueError(INPUT_SOURCE_ERROR_MESSAGE)

        # source records are read as bytes, and parsed one at a time during transform
        source_records: Iterator[bytes]
        if source_file:
            source_records = transformer_class.read_source_file(source_file)
        elif source_dataset:
            source_records = transformer_class.read_source_records_from_dataset(
                source, source_dataset
            )
        elif source_parquet:
            source_records = transformer_class.read_source_records_from_parquet(
                source, source_parquet
            )

        return transformer_class(
            source,
            source_records,
            exclusion_list_path,
            source_file=source_file,
            source_dataset=source_dataset,
            source_parquet=source_parquet,
            run_id=run_id,
            run_timestamp=run_timestamp,
        )

    @staticmethod
    def get_run_data(
        source: str,
        source_file: str | None = None,
        source_dataset: str | None = None,
        source_parquet: str | None = None,
        run_id: str | None = None,
        run_timestamp: str | None = None,
    ) -> dict:
        """Prepare dictionary of ETL run data based on the input source and CLI options.

        Run data is built in two steps:

        1. A default dictionary is created using the provided 'source', the current
           UTC date as 'run_date', and a 'run_type' of 'daily'. 'run_id' and
           'run_timestamp' use the provided values, or are minted (a UUID and the
           current UTC timestamp, respectively) if absent.
        2. Values are then overridden based on the input source:
            - 'source_file': 'source', 'run_date', and 'run_type' are parsed from
              the filename and replace the defaults.
            - 'source_dataset' or 'source_parquet': 'run_type' is set to 'patch'
              (see below).
            - neither: the defaults are returned as-is.

        A 'patch' run re-transforms the current source records in the TIMDEX dataset
        for a given source. A 'patch' run is typically performed after a transformer
        has been updated. The patched records become the current versions of
        those records, layered on top of the last 'full' run, *without* resetting the
        baseline that defines current records.

        Args:
            source: Source label (for example, "libguides").
            source_file: Filepath of the input source file.
                - example: "libguides-2024-06-03-full-extracted-records-to-index.xml"
            source_dataset: Location of the TIMDEX dataset with input source records.
            source_parquet: Location of parquet file(s) with input source records.
            run_id: A unique identifier associated with this ETL run.
                - example: "run-abc-123"
                - provided as CLI argument or minted if absent
            run_timestamp: A timestamp associated with this ETL run.
                - example: "2025-06-17T12:56:56.000000"
                - provided as CLI argument or minted if absent

        Raises:
            ValueError: If more than one input source is provided.

        Example output:
            {
                'source': 'libguides',
                'run_date': '2024-06-03',
                'run_type': 'full',
                'run_id': 'run-abc-123',
                'run_timestamp': '2024-06-17T12:56:56.000000+00:00'
            }
        """
        if len([i for i in (source_file, source_dataset, source_parquet) if i]) > 1:
            raise ValueError(INPUT_SOURCE_ERROR_MESSAGE)
        current_datetime = datetime.now(UTC)

        # set at default
        run_data = {
            "source": source,
            "run_date": current_datetime.strftime("%Y-%m-%d"),
            "run_type": "daily",
            "run_id": run_id or str(uuid.uuid4()),
            "run_timestamp": run_timestamp or current_datetime.isoformat(),
        }

        # if input source is a file, 'run_date' and 'run_type' are parsed from filename
        if source_file:
            run_data.update(Transformer._parse_run_data_from_source_file(source_file))

        # if input source is a dataset or parquet file(s), 'run_type' is set to patch
        elif source_dataset or source_parquet:
            run_data["run_type"] = "patch"

        return run_data

    @staticmethod
    def _parse_run_data_from_source_file(source_file: str) -> dict:
        # parse input source filename for run data information
        filename = source_file.rsplit("/", maxsplit=1)[-1]
        match_result = re.match(
            r"^([\w\-]+?)-(\d{4}-\d{2}-\d{2})-(\w+)-(\w+)-records-to-(.+?)(?:_(\d+))?\.(\w+)$",
            filename,
        )
        if not match_result:
            message = f"Provided S3 URI or filename is invalid: {filename}."
            raise ValueError(message)

        match_keys = [
            "source",
            "run_date",
            "run_type",
            "stage",
            "action",
            "index",
            "file_type",
        ]
        output_keys = ["source", "run_date", "run_type"]
        try:
            filename_parts = dict(zip(match_keys, match_result.groups(), strict=True))
            run_data = {k: v for k, v in filename_parts.items() if k in output_keys}
        except ValueError as exception:
            message = (
                f"Input S3 URI or filename '{filename}' does not contain required "
                f"dataset data: {exception}."
            )
            raise ValueError(message) from exception

        return run_data

    def serialize_source_record(
        self, source_record: Tag | etree._Element | dict
    ) -> bytes | None:
        """Serialize an already parsed source record, for storing in the dataset.

        Source records read as bytes are stored as-is; this is only used when a
        transformer is given already parsed records.
        """
        if isinstance(source_record, Tag):
            return source_record.encode()
        if isinstance(source_record, etree._Element):  # noqa: SLF001
            return etree.tostring(source_record, encoding="utf-8", with_tail=False)
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
        if self.record_is_excluded(source_record):
            source_record_id = self.get_source_record_id(source_record)
            logger.debug(f"Record ID {source_record_id} is excluded, skipping.")
            raise SkippedRecordEvent(source_record_id)

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

    def record_is_excluded(self, _source_record: dict[str, JSON] | Tag) -> bool:
        """
        Determine whether a source record should be excluded.

        Args:
            source_record: A single source record.
        """
        return False

    def write_to_timdex_dataset(self, dataset_location: str) -> list:
        """Write output to TIMDEX dataset."""
        timdex_dataset = TIMDEXDataset(location=dataset_location)
        return timdex_dataset.records.write(rows_iter=self)

    def write_to_file(self, output_file: str) -> int:
        """Write transformed records to a JSONLines file, one record per line.

        Only records with action 'index' are written.  Deleted, skipped, and errored
        records are counted and logged as usual, but not written.

        Args:
            output_file: Local or S3 filepath to write to.
        """
        count = 0
        with smart_open.open(output_file, "wb") as file:
            for record in self:
                if record.action == "index":
                    file.write(record.transformed_record + b"\n")
                    count += 1
        logger.info(f"File write complete - records: {count}, file: {output_file}")
        return count

    def write_to_parquet_files(self, output_location: str) -> list[str]:
        """Write output to a directory of parquet files.

        The schema very closely mirrors the TIMDEX Dataset schema.

        Args:
            output_location: Local or S3 directory to write parquet files to.  Must be
                empty or not yet exist.
        """
        filesystem, path = _parse_location(output_location)
        written_files: list[ds.WrittenFile] = []
        ds.write_dataset(
            self._create_parquet_files_batches(),
            base_dir=path,
            basename_template="part-{i}.parquet",
            existing_data_behavior="error",
            file_options=ds.ParquetFileFormat().make_write_options(
                compression=PARQUET_FILES_COMPRESSION
            ),
            file_visitor=written_files.append,
            filesystem=filesystem,
            format="parquet",
            max_rows_per_file=PARQUET_FILES_MAX_ROWS_PER_FILE,
            max_rows_per_group=PARQUET_FILES_ROW_GROUP_SIZE,
            preserve_order=True,
            schema=PARQUET_FILES_SCHEMA,
        )

        total_rows = sum(written_file.metadata.num_rows for written_file in written_files)
        logger.info(
            f"Parquet files write complete - files: {len(written_files)}, "
            f"rows: {total_rows}"
        )
        return [written_file.path for written_file in written_files]

    def _create_parquet_files_batches(self) -> Iterator[pa.RecordBatch]:
        """Yield record batches, each one parquet row group, of transformed records."""
        for batch in itertools.batched(self, PARQUET_FILES_ROW_GROUP_SIZE, strict=False):
            yield pa.RecordBatch.from_pylist(
                [
                    {name: getattr(record, name) for name in PARQUET_FILES_SCHEMA.names}
                    | {
                        "transformed_record": (
                            record.transformed_record.decode()
                            if record.transformed_record
                            else None
                        )
                    }
                    for record in batch
                ],
                schema=PARQUET_FILES_SCHEMA,
            )

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
    def read_source_file(cls, source_file: str) -> Iterator[bytes]:
        """
        Read source file and yield each source record as bytes, without parsing.

        Must be overridden by format subclasses.

        Args:
            source_file: A file containing source records to be transformed.
        """

    @classmethod
    def parse_source_file(cls, source_file: str) -> Iterator[dict[str, JSON] | Tag]:
        """
        Read source file and yield each source record parsed.

        Args:
            source_file: A file containing source records to be transformed.
        """
        for source_record in cls.read_source_file(source_file):
            yield cls.parse_source_record(source_record)

    @classmethod
    @abstractmethod
    def parse_source_record(cls, source_record: bytes) -> dict[str, JSON] | Tag:
        """
        Parse a single serialized source record into its format-specific type.

        Must be overridden by format subclasses.

        Args:
            source_record: A source record as bytes, as stored in a TIMDEX dataset.
        """

    @classmethod
    def read_source_records_from_dataset(
        cls, source: str, source_dataset: str
    ) -> Iterator[bytes]:
        """Read current source records from a TIMDEX dataset, as bytes.

        Records are parsed during transformation by the format-specific
        `parse_source_record` method.

        Args:
            source_dataset: Location of TIMDEX dataset with source records.
        """
        timdex_dataset = TIMDEXDataset(source_dataset)

        for record in timdex_dataset.records.read_dicts_iter(
            table="current_records",
            columns=["source_record"],
            source=source,
            action="index",
        ):
            yield record["source_record"]

    @classmethod
    def read_source_records_from_parquet(
        cls, source: str, source_parquet: str
    ) -> Iterator[bytes]:
        """Read source records from parquet file(s), as bytes.

        The parquet file(s) must have the TIMDEX records columns 'source_record',
        'source', and 'action'.  A directory is read recursively, in sorted path order,
        ignoring non-parquet files.  Only rows for the given source with action 'index'
        are read, in file order.

        Args:
            source: Source label to filter rows by.
            source_parquet: Local or S3 location of a parquet file or directory.
        """
        filesystem, path = _parse_location(source_parquet)
        dataset = ds.dataset(
            path,
            filesystem=filesystem,
            format="parquet",
            exclude_invalid_files=True,
        )
        logger.info(f"Reading source records from {len(dataset.files)} parquet file(s)")

        for batch in dataset.to_batches(
            columns=["source_record"],
            filter=(pc.field("source") == source) & (pc.field("action") == "index"),
            batch_size=PARQUET_DATASET_BATCH_SIZE,
        ):
            yield from batch.column("source_record").to_pylist()

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


def _parse_location(location: str) -> tuple[fs.FileSystem, str]:
    """Return a pyarrow filesystem and path for a local or S3 location."""
    if location.startswith("s3://"):
        return fs.S3FileSystem(), location.removeprefix("s3://")
    return fs.LocalFileSystem(), os.path.abspath(location)
