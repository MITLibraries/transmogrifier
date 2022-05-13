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
    def create_source_record_id(cls, xml: Tag) -> str:
        """
        Create a source record ID from a Zenodo Datacite XML record. This method
        is subclassed from the Datacite class as more parsing required for
        Zenodo identifiers.
        Args:
            xml: A BeautifulSoup Tag representing a single Datacite record in
            oai_datacite XML.
        """
        source_record_id = xml.header.find("identifier").string.replace(
            "oai:zenodo.org:", ""
        )
        return source_record_id
