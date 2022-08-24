import logging

from bs4 import Tag

from transmogrifier.sources.transformer import Transformer

logger = logging.getLogger(__name__)


class Ead(Transformer):
    """EAD transformer."""

    @classmethod
    def get_main_titles(cls, xml: Tag) -> list[Tag]:
        """
        Retrieve main title(s) from an EAD XML record.

        Overrides metaclass get_main_titles() method.

        Args:
            xml: A BeautifulSoup Tag representing a single EAD XML record.
        """
        main_titles = []
        for titlestmt in xml.find_all("titlestmt"):
            titles = " ".join(
                string
                for titleproper in titlestmt.find_all("titleproper")
                for string in titleproper.stripped_strings
            )
            subtitles = " ".join(
                string
                for subtitle in titlestmt.find_all("subtitle")
                for string in subtitle.stripped_strings
            )
            if subtitles:
                subtitles = ": " + subtitles
            main_titles.append(titles + subtitles)
        return main_titles

    @classmethod
    def get_source_record_id(cls, xml: Tag) -> str:
        """
        Get the source record ID from an EAD XML record.

        Overrides metaclass get_source_record_id() method.

        Args:
            xml: A BeautifulSoup Tag representing a single EAD XML record.
        """
        return xml.header.identifier.string.replace("oai:mit//", "")
