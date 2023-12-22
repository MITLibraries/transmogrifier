import logging
from datetime import datetime
from typing import Optional

from transmogrifier.config import DATE_FORMATS

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


def parse_geodata_string(geodata_string: str, source_record_id: str) -> list[float]:
    """Get list of values from a formatted geodata string.

    Example:
     - "ENVELOPE(-111.1, -104.0, 45.0, 40.9)"
     - "POLYGON((-80 25, -65 18, -64 33, -80 25))"

     Args:
        geodata_string: Formatted geodata string to parse.
        source_record_id: The ID of the record containing the string to parse.
    """
    geodata_points = []
    try:
        raw_geodata_points = geodata_string.split("(")[-1].split(")")[0].split(",")
        stripped_geodata_points = map(str.strip, raw_geodata_points)
        geodata_floats = list(map(float, stripped_geodata_points))
        geodata_points.extend(geodata_floats)
    except ValueError:
        message = (
            f"Record ID '{source_record_id}': "
            f"Unable to parse geodata string '{geodata_string}'"
        )
        raise ValueError(message)
    return geodata_points


def parse_solr_date_range_string(
    date_range_string: str, source_record_id: str
) -> list[str]:
    """Get a list of values from a Solr-formatted date range string.

    Example:
     - "[1943 TO 1946]"

    Args:
        date_range_string: Formatted date range string to parse.
        source_record_id: The ID of the record containing the string to parse.
    """
    date_ranges = []
    if (
        date_range_string.startswith("[")
        and date_range_string.endswith("]")
        and " TO " in date_range_string
    ):
        date_range_values = date_range_string.split("[")[-1].split("]")[0].split(" TO ")
        if [date_range_string] != date_range_values:
            date_ranges.extend(date_range_values)
    else:
        message = (
            f"Record ID '{source_record_id}': "
            f"Unable to parse date range string '{date_range_string}'"
        )
        raise ValueError(message)
    return date_ranges


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


class DeletedRecord(Exception):
    """Exception raised for records with a deleted status.

    Attributes:
        timdex_record_id: The TIMDEX record ID (not the source record ID) for the record

    """

    def __init__(self, timdex_record_id):
        self.timdex_record_id = timdex_record_id
