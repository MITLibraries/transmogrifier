import json
import logging
import os
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from attrs import asdict
from smart_open import open

from transmogrifier.config import DATE_FORMATS
from transmogrifier.models import TimdexRecord

# import XmlTransformer only when type checking to avoid circular dependency
if TYPE_CHECKING:  # pragma: no cover
    from transmogrifier.sources.transformer import Transformer

logger = logging.getLogger(__name__)


def generate_citation(extracted_data: dict) -> str:
    """Generate a citation in the Datacite schema format.

    extracted_data: A dict of data extracted from a source record, in the format that
        would be passed as kwargs to the TimdexRecord class (see return value from the
        `create_from_<source>_xml()` method of any source transform class).
    """
    citation = ""
    title = extracted_data["title"]
    url_string = f" {extracted_data['source_link']}"

    if not extracted_data.get("contributors"):
        creator_string = None
    else:
        creator_names = [
            contributor.value
            for contributor in extracted_data["contributors"]
            if (contributor.kind and contributor.kind.lower() == "author")
            or (contributor.kind and contributor.kind.lower() == "creator")
        ]
        creator_string = (", ").join(creator_names)

    if not extracted_data.get("dates"):
        publication_dates = None
    else:
        publication_dates = [
            date.value
            for date in extracted_data["dates"]
            if date.kind == "Publication date" and date.value
        ]

    if creator_string and publication_dates:
        citation += f"{creator_string} ({publication_dates[0]}): {title}."
    elif creator_string and not publication_dates:
        citation += f"{creator_string.rstrip('.')}. {title}."
    elif publication_dates and not creator_string:
        citation += f"{title}. {publication_dates[0]}."
    else:
        citation += f"{title}."

    publisher_field = extracted_data.get("publication_information")
    publisher_string = f" {publisher_field[0]}." if publisher_field else ""

    resource_types = extracted_data.get("content_type")
    resource_type_string = f" {(', ').join(resource_types)}." if resource_types else ""

    citation += publisher_string + resource_type_string + url_string
    return citation


def parse_date_from_string(
    date_string: str,
) -> Optional[datetime]:
    """
    Transform a date string into a datetime object according to one of the configured
    OpenSearch date formats. Returns None if the date string cannot be parsed.

    Args:
        date_string: A date string.
    """
    for date_format in DATE_FORMATS:
        try:
            return datetime.strptime(date_string, date_format)
        except ValueError:
            pass
    return None


def validate_date(
    date_string: str,
    source_record_id: str,
) -> bool:
    """
    Validate that a date string can be parsed according to one of the configured
    OpenSearch date formats. Returns True if date string is valid or returns
    False and logs an error.

    Args:
        date_string: A date string.
        source_record_id: The ID of the record being transformed.
    """
    if parse_date_from_string(date_string):
        return True
    else:
        logger.debug(
            "Record ID '%s' has a date that couldn't be parsed: '%s'",
            source_record_id,
            date_string,
        )
        return False


def validate_date_range(
    start_date: str,
    end_date: str,
    source_record_id: str,
) -> bool:
    """
    Validate a date range by validating that the start and end dates can be parsed and
    ensuring that the start date is before the end date to avoid an OpenSearch exception.
    Returns true if only one date exists in the range or the end date is after the start
    date, otherwise returns False and logs an error.

    Args:
        start_date: The start date of a date range.
        end_date: The end date of a date range.
        source_record_id: The ID of the record being transformed.
    """
    start_date_object = parse_date_from_string(start_date)
    end_date_object = parse_date_from_string(end_date)
    if start_date_object and end_date_object:
        if start_date_object <= end_date_object:
            return True
        else:
            logger.debug(
                "Record ID '%s' has a later start date than end date: '%s', '%s'",
                source_record_id,
                start_date,
                end_date,
            )
            return False
    else:
        logger.debug(
            "Record ID '%s' has invalid values in a date range: '%s', '%s'",
            source_record_id,
            start_date,
            end_date,
        )
        return False


def write_deleted_records_to_file(deleted_records: list[str], output_file_path: str):
    with open(output_file_path, "w") as file:
        for record_id in deleted_records:
            file.write(f"{record_id}\n")


def write_timdex_records_to_json(
    transformer_instance: "Transformer", output_file_path: str
) -> int:
    count = 0
    try:
        record: TimdexRecord = next(transformer_instance)
    except StopIteration:
        return count
    with open(output_file_path, "w") as file:
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
                    "Status update: %s records written to output file so far!", count
                )
            try:
                record: TimdexRecord = next(transformer_instance)  # type: ignore[no-redef]  # noqa: E501
            except StopIteration:
                break
            file.write(",\n")
        file.write("\n]")
    return count


class DeletedRecord(Exception):
    """Exception raised for records with a deleted status.

    Attributes:
        timdex_record_id: The TIMDEX record ID (not the source record ID) for the record

    """

    def __init__(self, timdex_record_id):
        self.timdex_record_id = timdex_record_id
