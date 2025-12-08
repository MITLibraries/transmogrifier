import logging

from bs4 import Tag  # type: ignore[import-untyped]

from transmogrifier.sources.xml.springshare import SpringshareOaiDc

logger = logging.getLogger(__name__)


class LibGuides(SpringshareOaiDc):
    """LibGuides transformer that extends SpringshareOaiDc."""

    def record_is_excluded(self, source_record: Tag) -> bool:
        """
        Determine whether a source record should be excluded.

        Args:
            source_record: A single source record.
        """
        source_link = self.get_source_link(source_record)
        excluded = source_link in self.exclusion_list if self.exclusion_list else False
        if excluded:
            logger.info(
                f"Record ID {self.get_source_record_id(source_record)} with source link "
                f"'{source_link}' excluded"
            )
        return excluded

    @classmethod
    def get_contributors(cls, _source_record: Tag) -> None:
        """
        Override get_contributors to always return None for LibGuides records.

        Args:
            _source_record: A BeautifulSoup Tag representing a
                single OAI DC record in XML.
        """
        return None  # noqa: RET501
