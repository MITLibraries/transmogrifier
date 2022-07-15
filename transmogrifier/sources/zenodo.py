from typing import List

from bs4 import Tag

from transmogrifier.sources.datacite import Datacite


class Zenodo(Datacite):
    """Zenodo transformer class."""

    @classmethod
    def get_source_record_id(cls, xml: Tag) -> str:
        """
        Get the source record ID from a Zenodo Datacite XML record.

        Overrides the base Datacite.get_source_record_id() method.

        Args:
            xml: A BeautifulSoup Tag representing a single Zenodo record in
                oai_datacite XML.
        """
        return xml.header.find("identifier").string.replace("oai:zenodo.org:", "")

    @classmethod
    def valid_content_types(cls, content_type_list: List[str]) -> bool:
        """
        Validate a list content_type values from a Datacite XML record.

        Overrides the base Datacite.valid_content_types() method.

        Args:
            content_type_list: A list of content_type values.
        """
        if content_type_list[0] in [
            "lesson",
            "poster",
            "presentation",
            "publication",
        ]:
            return False
        else:
            return True
