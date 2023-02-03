import json
import logging
import os
from datetime import datetime
from typing import Iterator, Optional

from attrs import asdict
from bs4 import BeautifulSoup, Tag

# Note: the lxml module in defusedxml is deprecated, so we have to use the
# regular lxml library. Transmogrifier only parses data from known sources so this
# should not be a security issue.
from lxml import etree  # nosec B410
from smart_open import open

from transmogrifier.config import DATE_FORMATS
from transmogrifier.models import TimdexRecord

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


def parse_xml_records(
    input_file_path: str,
) -> Iterator[Tag]:
    with open(input_file_path, "rb") as file:
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


def format_date(
    date_value: Optional[str],
) -> Optional[datetime]:
    """
    Format a date value as a datetime object according to one of the configured
    OpenSearch date formats.

    Args:
        date_value: A date value.
        source_record_id: The ID of the record being transformed.
    """
    if date_value:
        for date_format in DATE_FORMATS:
            try:
                return datetime.strptime(date_value, date_format)
            except ValueError:
                pass
    return None


def validate_date(
    date_value: Optional[str],
    source_record_id: str,
) -> Optional[str]:
    """
    Validate that a date can be parsed according to one of the configured
    OpenSearch date formats. Returns original date value if valid or returns
    None and logs an error.

    Args:
        date_value: A date value.
        source_record_id: The ID of the record being transformed.
    """
    if date_value:
        date_value = date_value.strip()
        try:
            if format_date(date_value):
                return date_value
        except ValueError:
            pass
    logger.error(
        "Record # %s has a date that couldn't be parsed: %s",
        source_record_id,
        date_value,
    )
    return None


def validate_date_range(
    gte_date: Optional[str],
    lte_date: Optional[str],
    source_record_id: str,
) -> bool:
    """
    Validate a date range by ensuring that the start date is before the end date to avoid
    an OpenSearch exception. Returns true if only one date exists in the range or the end
    date is after the start date, otherwise returns False and logs an error.

    Args:
        gte_date: The start date of a date range.
        lte_date: The end date of a date range.
        source_record_id: The ID of the record being transformed.
    """
    formatted_gte_date = format_date(gte_date)
    formatted_lte_date = format_date(lte_date)
    if formatted_gte_date and formatted_lte_date:
        date_diff = formatted_gte_date - formatted_lte_date
        if date_diff.days < 0:
            return True
        else:
            logger.error(
                "Record ID %s contains an invalid date range: %s, %s",
                source_record_id,
                gte_date,
                lte_date,
            )
            return False
    return True


def write_deleted_records_to_file(deleted_records: list[str], output_file_path: str):
    with open(output_file_path, "w") as file:
        for record_id in deleted_records:
            file.write(f"{record_id}\n")


def write_timdex_records_to_json(
    records: Iterator[TimdexRecord], output_file_path: str
) -> int:
    count = 0
    try:
        record = next(records)
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
                record = next(records)
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
