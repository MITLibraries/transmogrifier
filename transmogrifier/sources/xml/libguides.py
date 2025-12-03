from bs4 import Tag  # type: ignore[import-untyped]

from transmogrifier.sources.xml.springshare import SpringshareOaiDc


class LibGuides(SpringshareOaiDc):
    """LibGuides transformer that extends SpringshareOaiDc."""

    @classmethod
    def get_contributors(cls, _source_record: Tag) -> None:
        """
        Override get_contributors to always return None for LibGuides records.

        Args:
            _source_record: A BeautifulSoup Tag representing a
                single OAI DC record in XML.
        """
