from bs4 import Tag

from transmogrifier.sources.datacite import Datacite


class Zenodo(Datacite):
    """Zenodo transformer class."""

    @classmethod
    def create_source_record_id(cls, xml: Tag) -> str:
        """
        Create a source record ID from a Zenodo Datacite XML record.

        Overrides the base Datacite.create_source_record_id() method.

        Args:
            xml: A BeautifulSoup Tag representing a single Datacite XML record.
        """
        source_record_id = xml.header.find("identifier").string.replace(
            "oai:zenodo.org:", ""
        )
        return source_record_id
