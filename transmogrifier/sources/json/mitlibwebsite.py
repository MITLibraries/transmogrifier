import base64
import hashlib
import logging
from functools import lru_cache

from bs4 import BeautifulSoup, Tag

import transmogrifier.models as timdex
from transmogrifier.sources.jsontransformer import JSONTransformer
from transmogrifier.sources.transformer import JSON

logger = logging.getLogger(__name__)


class MITLibWebsite(JSONTransformer):

    @classmethod
    @lru_cache(maxsize=8)
    def parse_html(cls, html_base64: str) -> Tag:
        """Parse HTML from base64 encoded ASCII string.

        For this mitlibwebsite source, also remove the <header> and <footer> elements
        which are not helpful for any metadata or fulltext purposes.

        This method utilizes an LRU cache to only parse the HTML once per unique HTML
        base64 string passed.  Maxsize is set to 8 to ensure the cache is large enough
        for 8 concurrent transformations if threading is used (increase if needed for
        more threads).
        """
        html_bytes = base64.b64decode(html_base64)
        html_soup = BeautifulSoup(html_bytes, "html.parser")

        # remove header and footer
        if header := html_soup.select_one("body > header"):
            header.decompose()
        if footer := html_soup.select_one("body > footer"):
            footer.decompose()

        return html_soup

    @classmethod
    def get_main_titles(cls, source_record: dict) -> list[str]:
        """
        Retrieve main title(s) from a JSON record.

        Must be overridden by source subclasses.

        Args:
            source_record: A JSON object representing a source record.
        """
        if source_record["cdx_title"] is None:
            return []
        return [source_record["cdx_title"]]

    def get_source_link(self, source_record: dict) -> str:
        """Set source link for the item.

        Unlike other Transmogrifier sources that dynamically build a source link,
        MITLibWebsite files are expected to have a fully formed and appropriate
        source link in the metadata already.  This method relies on that data.
        """
        return source_record["url"]

    def get_timdex_record_id(self, source_record: dict) -> str:
        """Set the TIMDEX record ID.

        Concatenate the source name + source record id.
        """
        return f"{self.source}:{self.get_source_record_id(source_record)}"

    @classmethod
    def get_source_record_id(cls, source_record: dict) -> str:
        """Get or generate a source record ID from a JSON record.

        In the case of records from browsertrix-harvester, the website URL
        is the most unique and consistent identifier for a source record.
        While a great identifier, URLs makes a poor 'timdex_record_id' given
        the special characters and its length, hence the MD5 hash.

        Args:
            source_record: A JSON object representing a source record.
        """
        data_string = source_record["url"].encode()
        return hashlib.md5(data_string, usedforsecurity=False).hexdigest()

    @classmethod
    def record_is_deleted(cls, source_record: dict[str, JSON]) -> bool:
        """
        Determine whether record has a status of deleted.

        Args:
            source_record: A JSON object representing a source record.
        """
        return source_record.get("status") == "deleted"

    @classmethod
    def get_content_type(cls, _source_record: dict) -> list[str]:
        return ["Website"]

    @classmethod
    def get_contributors(cls, _source_record: dict) -> list[timdex.Contributor]:
        return [
            timdex.Contributor(value="MIT Libraries", kind="creator", mit_affiliated=True)
        ]

    def get_dates(self, _source_record: dict) -> list[timdex.Date]:
        return [timdex.Date(value=self.run_data["run_timestamp"], kind="Accessed")]

    def get_format(self, _source_record: dict) -> str:
        return "electronic resource"

    def get_fulltext(self, source_record: dict) -> str:
        html_soup = self.parse_html(source_record["html_base64"])
        return html_soup.get_text(separator=" ", strip=True)

    @classmethod
    def get_links(cls, source_record: dict) -> list[timdex.Link]:
        return [timdex.Link(url=source_record["url"], kind="Website")]

    @classmethod
    def get_summary(cls, source_record: dict) -> list[str] | None:
        html_soup = cls.parse_html(source_record["html_base64"])

        og_tag = html_soup.find("meta", attrs={"property": "og:description"})
        if not og_tag:
            return None

        content = og_tag.get("content", "").strip()
        if content == "":
            return None

        return [content]
