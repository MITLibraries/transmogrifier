import logging
from datetime import UTC, datetime

import smart_open  # type: ignore[import-untyped]

import transmogrifier.models as timdex
from transmogrifier.config import DATE_FORMATS

logger = logging.getLogger(__name__)


def generate_citation(timdex_record: timdex.TimdexRecord) -> str:
    """Generate a citation in the Datacite schema format.

    timdex_record: A TimdexRecord instance from which to generate a citation.
    """
    citation = ""
    title = timdex_record.title
    url_string = f" {timdex_record.source_link}"

    creator_string = ""
    if timdex_record.contributors:
        creator_names = [
            contributor.value
            for contributor in timdex_record.contributors
            if (contributor.kind and contributor.kind.lower() == "author")
            or (contributor.kind and contributor.kind.lower() == "creator")
        ]
        creator_string = (", ").join(creator_names)

    publication_dates = ""
    if dates := timdex_record.dates:
        publication_dates = [  # type: ignore[assignment]
            date.value for date in dates if date.kind == "Publication date" and date.value
        ]

    if creator_string and publication_dates:
        citation += f"{creator_string} ({publication_dates[0]}): {title}."
    elif creator_string and not publication_dates:
        citation += f"{creator_string.rstrip('.')}. {title}."
    elif publication_dates and not creator_string:
        citation += f"{title}. {publication_dates[0]}."
    else:
        citation += f"{title}."

    publisher_string = ""
    if publishers_field := timdex_record.publishers:
        if publisher_location := publishers_field[0].location:
            publisher_string = f" {publisher_location} :"
        if publisher_name := publishers_field[0].name:
            publisher_string += f" {publisher_name}."

    resource_types = timdex_record.content_type
    resource_type_string = f" {(', ').join(resource_types)}." if resource_types else ""

    citation += publisher_string + resource_type_string + url_string
    return citation


def parse_date_from_string(
    date_string: str,
) -> datetime | None:
    """
    Transform a date string into a datetime object according to one of the configured
    OpenSearch date formats. Returns None if the date string cannot be parsed.

    Args:
        date_string: A date string.
    """
    for date_format in DATE_FORMATS:
        try:
            return datetime.strptime(date_string, date_format).astimezone(UTC)
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
        logger.debug(
            "Record ID '%s' has a later start date than end date: '%s', '%s'",
            source_record_id,
            start_date,
            end_date,
        )
        return False
    logger.debug(
        "Record ID '%s' has invalid values in a date range: '%s', '%s'",
        source_record_id,
        start_date,
        end_date,
    )
    return False


def load_exclusion_list(
    exclusion_list_path: str,
) -> list[str]:
    """
    Load a CSV file from path (S3 or local filesystem) and return values as a list.

    CSV file has no headers and contains identifiers to exclude, one per line.

    Args:
        exclusion_list_path: Path to exclusion list file (s3://bucket/key or local path).
    """
    with smart_open.open(exclusion_list_path, "r") as exclusion_list:
        rows = exclusion_list.readlines()
    exclusion_list = [row.strip() for row in rows if row.strip()]
    logger.info(
        f"Loaded exclusion list from {exclusion_list_path} with {len(exclusion_list)} "
        "entries"
    )
    logger.debug(exclusion_list)
    return exclusion_list
