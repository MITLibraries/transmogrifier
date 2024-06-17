from bs4 import Tag  # type: ignore[import-untyped]

from transmogrifier.exceptions import SkippedRecordEvent
from transmogrifier.sources.xml.dspace_dim import DspaceDim

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
    def get_content_type(cls, source_record: Tag) -> list[str] | None:
        content_types = [
            str(content_type.string)
            for content_type in source_record.find_all(
                "dim:field", element="type", string=True
            )
        ] or ["no content type in source record"]
        if cls.valid_content_types(content_types):
            return content_types
        message = f'Record skipped based on content type: "{content_types}"'
        raise SkippedRecordEvent(message, cls.get_source_record_id(source_record))

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
        return True
