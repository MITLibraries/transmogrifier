from typing import Iterator

from bs4 import Tag

from transmogrifier.sources.datacite import Datacite


class Zenodo(Datacite):
    def __init__(
        self,
        source: str,
        source_base_url: str,
        source_name: str,
        input_records: Iterator[Tag],
    ):
        super().__init__(source, source_base_url, source_name, input_records)

    @classmethod
    def create_source_link(cls, source_base_url: str, source_record_id: str) -> str:
        """
        Args:
            source_record_id: The source record ID from which direct links to source
            metadata records can be constructed.
            source_base_url: The base URL for the source system from which direct links
            to source metadata records can be constructed.
        """
        source_link = source_base_url + source_record_id.replace("oai:zenodo.org:", "")
        return source_link
