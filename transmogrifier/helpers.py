import json
from typing import Iterator

from attrs import asdict
from bs4 import BeautifulSoup, Tag
from smart_open import open

from transmogrifier.models import TimdexRecord


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
