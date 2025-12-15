"""Transformer module."""

# ruff: noqa: D417

from __future__ import annotations

import json
import logging
import os
import re
import uuid
from abc import ABC, abstractmethod
from datetime import date, datetime
from importlib import import_module
from typing import TYPE_CHECKING, final

import smart_open  # type: ignore[import-untyped]
from bs4 import Tag  # type: ignore[import-untyped]
from timdex_dataset_api import (  # type: ignore[import-untyped, import-not-found]
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


class Transformer(ABC):
    """Base transformer class."""

    @final
    def __init__(
        self,
        source: str,
        source_records: Iterator[dict[str, JSON] | Tag],
        exclusion_list_path: str | None = None,
        source_file: str | None = None,
        run_id: str | None = None,
        run_timestamp: str | None = None,
    ) -> None:
        """
        Initialize Transformer instance.

        Args:
            source: Source repository label. Must match a source key from config.SOURCES.
            exclusion_list_path: S3 or local filepath to exclusion list CSV file.
            exclsion_list: The exclusion list for this particular source.
            source_records: A set of source records to be processed.
            source_file: Filepath of the input source file.
            run_id: A unique identifier associated with this ETL run.
            run_timestamp: A timestamp associated with this ETL run.
        """
        self.source: str = source
        self.exclusion_list_path: str | None = exclusion_list_path
        self._exclusion_list: list[str] | None = None
        self.source_base_url: str = SOURCES[source]["base-url"]
        self.source_name = SOURCES[source]["name"]
        self.source_records: Iterator[JSON | Tag] = source_records
        self.processed_record_count: int = 0
        self.transformed_record_count: int = 0
        self.skipped_record_count: int = 0
        self.error_record_count: int = 0
        self.deleted_records: list[str] = []
        self.source_file = source_file

        self.run_data = self.get_run_data(
            source_file,
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
            with smart_open.open(self.exclusion_list_path, "r") as exclusion_list:
                rows = exclusion_list.readlines()
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
        return self

    @final
    def __next__(self) -> DatasetRecord:
        """Return next transformed record."""
        while True:
            transformed_record = None
            timdex_record_id = None

            source_record = next(self.source_records)
            self.processed_record_count += 1

            try:
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
                source_record=self.serialize_source_record(source_record),
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
        source_file: str,
        exclusion_list_path: str | None = None,
        run_id: str | None = None,
        run_timestamp: str | None = None,
    ) -> Transformer:
        """
        Instantiate specified transformer class and populate with source records.

        Args:
            source: Source repository label. Must match a source key from config.SOURCES.
            source_file: A file containing source records to be transformed.
            exclusion_list_path: CSV filepath to use for explicitly skipping records.
            run_id: A unique identifier associated with this ETL run.
            run_timestamp: A timestamp associated with this ETL run.
        """
        transformer_class = cls.get_transformer(source)
        source_records = transformer_class.parse_source_file(source_file)
        return transformer_class(
            source,
            source_records,
            exclusion_list_path,
            source_file=source_file,
            run_id=run_id,
            run_timestamp=run_timestamp,
        )

    @staticmethod
    def get_run_data(
        source_file: str | None,
        run_id: str | None = None,
        run_timestamp: str | None = None,
    ) -> dict:
        """Prepare dictionary of ETL run data based on input source filename and CLI args.

        If 'source_file' is None and a testing environment is detected, a mocked
        dictionary of run data will be returned.  This is primarily in place to remain
        backwards compatible tests that exercise transformation logic but have little to
        do with final outputs.

        Args:
            - source_file: str
                - example: "libguides-2024-06-03-full-extracted-records-to-index.xml"
            - run_id: str
                - example: "run-abc-123"
                - provided as CLI argument or minted if absent
            - run_timestamp: str
                - example: "2025-06-17T12:56:56.000000"
                - provided as CLI argument or minted if absent

        Example output:
            {
                'source': 'libguides',
                'run_date': '2024-06-03',
                'run_type': 'full',
                'run_id': 'run-abc-123'
            }
        """
        # if source_file is missing, but a testing context detected, mock run data
        if not source_file:
            if os.getenv("WORKSPACE") == "test":
                logger.warning(
                    "'source_file' is None, setting empty run data for test environment"
                )
                return {
                    "source": "placeholder",
                    "run_date": "2000-01-01",
                    "run_type": "daily",
                    "run_id": run_id or str(uuid.uuid4()),
                    "run_timestamp": "2000-01-01T00:00:00",
                }
            message = "'source_file' parameter is required outside of test environments"
            raise ValueError(message)

        # parse input source filename for run data information
        filename = source_file.split("/")[-1]
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

        # if run_id is not provided, mint one
        if not run_id:
            logger.info("explicit run_id not passed, minting new UUID")
            run_id = str(uuid.uuid4())
        message = f"run_id set: '{run_id}'"
        logger.info(message)
        run_data["run_id"] = run_id

        # if run_timestamp is not provided, mint one from run_date
        if not run_timestamp:
            logger.info("explicit run_id not passed, minting new UUID")
            run_timestamp = datetime.combine(
                date.fromisoformat(run_data["run_date"]),
                datetime.min.time(),
            ).isoformat()
        message = f"run_timestamp set: '{run_timestamp}'"
        logger.info(message)
        run_data["run_timestamp"] = run_timestamp

        return run_data

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
        if self.record_is_excluded(source_record):
            source_record_id = self.get_source_record_id(source_record)
            logger.info(
                f"Record ID {source_record_id} is in exclusion list, skipping record."
            )
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

    def write_to_parquet_dataset(self, dataset_location: str) -> list:
        """Write output to TIMDEX dataset."""
        timdex_dataset = TIMDEXDataset(location=dataset_location)
        return timdex_dataset.write(records_iter=self)

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
