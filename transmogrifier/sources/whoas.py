from transmogrifier.sources.dspace_dim import DspaceDim

INVALID_CONTENT_TYPES = [
    "Article",
    "Authority List",
    "Book",
    "Book chapter",
    "Course",
    "Preprint",
    "Presentation",
    "Technical Report",
    "Thesis",
    "Working Paper",
]


class Whoas(DspaceDim):
    """Whoas transformer class."""

    @classmethod
    def valid_content_types(cls, content_type_list: list[str]) -> bool:
        """
        Validate a list of content_type values from a DSpace DIM XML record.

        Overrides the base DspaceDim.valid_content_types() method.

        Args:
            content_type_list: A list of content_type values.
        """
        if all(item in INVALID_CONTENT_TYPES for item in content_type_list):
            return False
        else:
            return True
