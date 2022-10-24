import json
import logging
import os
from typing import Any, Dict, Iterator, Optional

from attrs import asdict
from bs4 import BeautifulSoup, Tag

# Note: the lxml module in defusedxml is deprecated, so we have to use the
# regular lxml library. Transmogrifier only parses data from known sources so this
# should not be a security issue.
from lxml import etree  # nosec B410
from smart_open import open

from transmogrifier.models import TimdexRecord

logger = logging.getLogger(__name__)


def crosswalk_value(
    crosswalk_dict: Dict[Any, Any], value: Optional[str]
) -> Optional[str]:
    """
    Crosswalk code to human-readable label based on the specified JSON crosswalk.

    Args:
        crosswalk_dict: A crosswalk dict of codes and replacement values.
        value: A value to be crosswalked.
    """
    if value in crosswalk_dict:
        value = crosswalk_dict[value]
    return value


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


def write_timdex_records_to_json(
    records: Iterator[TimdexRecord], output_file_path: str
) -> int:
    count = 0
    try:
        record = next(records)
    except StopIteration as error:
        raise ValueError("No records transformed from input file") from error
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
