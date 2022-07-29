from bs4 import Tag

from transmogrifier.sources.dspace_dim import DspaceDim

INVALID_CONTENT_TYPES = [
    "article",
    "authority list",
    "book",
    "book chapter",
    "course",
    "no content type in source record",
    "other",
    "preprint",
    "presentation",
    "technical report",
    "thesis",
    "text",
    "working paper",
]


class Whoas(DspaceDim):
    """Whoas transformer class."""

    @classmethod
    def get_content_types(cls, xml: Tag) -> list[str]:
        """
        Retrieve content types from a DSpace DIM XML record.

        Overrides the base DspaceDim.get_content_types() method.

        Args:
            xml: A BeautifulSoup Tag representing a single DSpace DIM XML record.
        """
        return [
            t.string for t in xml.find_all("dim:field", element="type", string=True)
        ] or ["no content type in source record"]

    @classmethod
    def valid_content_types(cls, content_type_list: list[str]) -> bool:
        """
        Validate a list of content_type values from a DSpace DIM XML record.

        Overrides the base DspaceDim.valid_content_types() method.

        Args:
            content_type_list: A list of content_type values.
        """
        if all(item.lower() in INVALID_CONTENT_TYPES for item in content_type_list):
            return False
        else:
            return True
