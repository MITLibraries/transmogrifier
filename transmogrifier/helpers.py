import json
from typing import Iterator

from attrs import asdict
from bs4 import BeautifulSoup, Tag
from smart_open import open

from transmogrifier.models import TimdexRecord


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
        print(extracted_data["contributors"])
        creator_names = [
            contributor.value
            for contributor in extracted_data["contributors"]
            if (contributor.kind and contributor.kind.lower() == "author")
            or (contributor.kind and contributor.kind.lower() == "creator")
        ]
        creator_string = (", ").join(creator_names)
        print(creator_string)

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
    print(citation)
    return citation


def parse_xml_records(input_file_path: str) -> Iterator[Tag]:
    with open(input_file_path, "r") as file:
        soup = BeautifulSoup(file, "xml")
        record = soup.record
        if record is None:
            raise ValueError("No records found in input file")
        yield record
        for record in record.find_next_siblings("record"):
            yield record


def write_timdex_records_to_json(
    records: Iterator[TimdexRecord], output_file_path: str
) -> int:
    count = 0
    with open(output_file_path, "w") as file:
        file.write("[\n")
        record = next(records)
        while record:
            count += 1
            file.write(
                json.dumps(
                    asdict(record, filter=lambda attr, value: value is not None),
                    indent=2,
                )
            )
            try:
                record = next(records)
            except StopIteration:
                break
            file.write(",\n")
        file.write("\n]")
    return count
