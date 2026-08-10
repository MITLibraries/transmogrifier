import base64
import logging
import re
from collections import defaultdict
from functools import lru_cache
from urllib.parse import urlparse

import pandas as pd
from bs4 import BeautifulSoup, Tag
from dateutil.parser import parse as date_parser

import transmogrifier.models as timdex
from transmogrifier.exceptions import SkippedRecordEvent
from transmogrifier.helpers import LibGuidesAPIClient
from transmogrifier.sources.jsontransformer import JSONTransformer
from transmogrifier.sources.transformer import JSON

logger = logging.getLogger(__name__)


# The following constants support logic for identifying LibGuides to exclude.
ALLOWED_TYPE_STATUS_PAIRS = [
    ("General Purpose Guide", "Published"),
    ("Course Guide", "Published"),
    ("Topic Guide", "Published"),
    ("Subject Guide", "Published"),
]
EXCLUDED_GROUPS = [
    3754,  # Internal staff guides
    32635,  # Records retention schedules
]
EXCLUDED_URL_REGEX = [
    r".*libguides.mit.edu/directory.*",  # staff directory main page
    r".*libguides.mit.edu/c.php\?g=176063.*",  # staff directory sub-pages
]


# instantiate a LibGuidesAPIClient singleton
libguides_api_client = LibGuidesAPIClient()


class LibGuides(JSONTransformer):
    """Transformer for Libguides originating from a Browsertrix-Harvester crawl.

    A web crawl is performed for Libguides via the Browsertrix-Harvester. In addition to
    this data, the LibGuidesAPIClient is used to pull some metadata about the guides
    via an API.  This transformer uses both data sources to construct records for TIMDEX.
    """

    # attach LibGuidesAPIClient singleton to class
    api_client = libguides_api_client

    # cached class level property
    _allowed_guides_df: pd.DataFrame | None = None

    @property
    def allowed_guides_df(self) -> pd.DataFrame:
        """Cached dataframe of allowed guides."""
        if self._allowed_guides_df is None:
            self._allowed_guides_df = self._filter_allowed_guides()
        return self._allowed_guides_df

    def _filter_allowed_guides(
        self,
        allowed_types: list[tuple[str, str]] | None = None,
        excluded_group_ids: list[int] | None = None,
    ) -> pd.DataFrame:
        if not allowed_types:
            allowed_types = ALLOWED_TYPE_STATUS_PAIRS
        if not excluded_group_ids:
            excluded_group_ids = EXCLUDED_GROUPS

        # filter by allowed (type_label, status_label) combos
        type_status_pairs = self.api_client.api_guides_df[
            ["type_label", "status_label"]
        ].apply(tuple, axis=1)
        filtered_df = self.api_client.api_guides_df[type_status_pairs.isin(allowed_types)]

        # filter by excluded group IDs
        filtered_df = filtered_df[~filtered_df["group_id"].isin(excluded_group_ids)]

        # filter by excluded URL regex patterns
        for pattern in EXCLUDED_URL_REGEX:
            regex = re.compile(pattern)
            filtered_df = filtered_df[
                ~(
                    filtered_df["url"].str.match(regex, na=False)
                    | filtered_df["friendly_url"].str.match(regex, na=False)
                )
            ]

        logger.debug(
            f"Total guides: {len(self.api_client.api_guides_df)}, "
            f"filtered to {len(filtered_df)} allowed."
        )

        return filtered_df

    def record_is_excluded(self, source_record: dict) -> bool:
        """Determine if a single Guide is excluded.

        This method utilizes multiple private methods which check for specific things.  If
        any of them return True, the record is excluded.
        """
        return (
            self._excluded_per_non_libguides_domain(source_record)
            or self._excluded_per_allowed_rules(source_record)
            or self._excluded_per_missing_html(source_record)
            or self._exclude_sub_page_that_is_root_page(source_record)
        )

    @staticmethod
    def _excluded_per_non_libguides_domain(source_record: dict) -> bool:
        """Exclude a record if the captured URL is not from libguides.mit.edu."""
        parsed = urlparse(source_record["url"])
        return parsed.hostname != "libguides.mit.edu"

    def _excluded_per_allowed_rules(self, source_record: dict) -> bool:
        """Exclude a record if not present in allowed guides dataframe."""
        source_link = self.get_source_link(source_record)
        return not (
            (self.allowed_guides_df.url == source_link)
            | (self.allowed_guides_df.friendly_url == source_link)
        ).any()

    def _excluded_per_missing_html(self, source_record: dict) -> bool:
        """Exclude a record if the crawled HTML is empty (e.g. a redirect)."""
        return source_record["html_base64"].strip() == ""

    def _exclude_sub_page_that_is_root_page(self, source_record: dict) -> bool:
        """Exclude sub-pages that are effectively the guide root page.

        For guides that have sub-pages, e.g. `/foo`, there will be a sub-page that is
        effectively the root page itself.  These sub-pages will have a "position = 1"
        and "parent_id = 0" properties (i.e., a top-level page in the first position).
        These can be skipped.  Note that sub-pages can have sub-sub-pages as well.  These
        will have "position = 1" but a parent_id of the sub-page.  These should NOT be
        skipped as they are standalone, unique pages.
        """
        url = source_record["url"]

        try:
            guide = self.api_client.get_guide_by_url(url)
        except ValueError as exc:
            logger.warning(exc)
            return True  # if we cannot find URL in API data, skip (likely crawl noise)

        # if no position, assume root page and do NOT skip
        if pd.isna(guide.position):
            return False

        # if position = 1 and top-level page (parent_id = 0), skip
        return guide.position == "1" and guide.parent_id == "0"

    @classmethod
    @lru_cache(maxsize=8)
    def parse_html(cls, html_base64: str) -> Tag:
        """Parse HTML from base64 encoded ASCII string.

        This method utilizes an LRU cache to only parse the HTML once per unique HTML
        base64 string passed.
        """
        html_bytes = base64.b64decode(html_base64)
        return BeautifulSoup(html_bytes, "html.parser")

    @classmethod
    @lru_cache(maxsize=8)
    def extract_dublin_core_metadata(cls, html_base64: str) -> dict:
        """Extract DC metadata from the full Libguide HTML.

        This method utilizes an LRU cache to avoid re-parsing this data multiple times.
        """
        soup = cls.parse_html(html_base64)

        dc_metadata = defaultdict(list)

        # loop through all head.meta elements
        for meta in soup.find_all("meta"):
            name = meta.get("name")

            # skip those without a "DC." prefix
            if not name or not name.startswith("DC."):
                continue

            # extract DC element name
            name = name.removeprefix("DC.")

            # skip if not content
            content = meta.get("content")
            if not content or not content.strip():
                continue

            dc_metadata[name].append(content)

        return dict(dc_metadata)

    @classmethod
    def get_source_link(cls, source_record: dict) -> str:
        """Use the 'friendly' URL from LibGuides API data."""
        url = source_record["url"]
        try:
            guide = cls.api_client.get_guide_by_url(url)
        except ValueError:
            logger.warning("Could not find guide in API data for URL: %s", url)
            return url
        friendly_url = guide.get("friendly_url") or ""
        return friendly_url.strip() or url

    @classmethod
    def get_source_record_id(cls, source_record: dict) -> str:
        """Use numeric 'id' field from Libguides metadata with 'guides-' prefix."""
        try:
            guide = cls.api_client.get_guide_by_url(cls.get_source_link(source_record))
        except ValueError as exc:
            message = (
                "Could not determine source record ID, skipping record with URL: "
                f"{source_record['url']}"
            )
            logger.warning(message)
            raise SkippedRecordEvent(message) from exc
        return f"guides-{guide['id']}"

    def get_timdex_record_id(self, source_record: dict) -> str:
        return f"{self.source}:{self.get_source_record_id(source_record)}"

    @classmethod
    def get_main_titles(cls, source_record: dict) -> list[str]:
        dc_meta = cls.extract_dublin_core_metadata(source_record["html_base64"])

        # prefer DC title
        if dc_title := dc_meta.get("Title"):
            title = dc_title[0]

        # fallback on CDX title
        else:
            title = source_record["cdx_title"]

        # cleanup prefixes and suffixes
        title = title.removeprefix("Libguides: ")  # case-sensitive
        title = title.removeprefix("LibGuides: ")  # case-sensitive
        title = title.removeprefix("Home - ")
        title = title.removesuffix(" - LibGuides at MIT Libraries")
        title = title.removesuffix(": Home")

        return [title]

    @classmethod
    def record_is_deleted(cls, source_record: dict[str, JSON]) -> bool:
        return source_record.get("status") == "deleted"

    @classmethod
    def get_content_type(cls, _source_record: dict) -> list[str]:
        return ["LibGuide"]

    def get_dates(self, source_record: dict) -> list[timdex.Date]:
        # initialize with accessed date per web crawl
        dates = [
            timdex.Date(
                value=date_parser(self.run_data["run_timestamp"]).strftime("%Y-%m-%d"),
                kind="Accessed",
            )
        ]

        # add DC dates if present
        dc_meta = self.extract_dublin_core_metadata(source_record["html_base64"])
        for kind, key in (
            ("Created", "Date.Created"),
            ("Modified", "Date.Modified"),
        ):
            for raw in dc_meta.get(key, []):
                dates.append(  # noqa: PERF401
                    timdex.Date(
                        value=date_parser(raw).strftime("%Y-%m-%d"),
                        kind=kind,
                    )
                )

        return dates

    def get_format(self, _source_record: dict) -> str:
        return "electronic resource"

    def get_identifiers(self, source_record: dict) -> list[timdex.Identifier]:
        identifiers = []

        # add API data
        guide = self.api_client.get_guide_by_url(self.get_source_link(source_record))
        identifiers.extend(
            [
                timdex.Identifier(kind="LibGuide ID", value=str(guide["id"])),
            ]
        )

        # add any non-URL DC identifiers (those are saved in 'links' field)
        dc_meta = self.extract_dublin_core_metadata(source_record["html_base64"])
        for identifier in dc_meta.get("Identifier", []):
            if identifier.lower().startswith("http"):
                continue

            identifiers.append(timdex.Identifier(value=identifier))

        return identifiers

    @classmethod
    def get_links(cls, source_record: dict) -> list[timdex.Link] | None:
        links = []
        dc_meta = cls.extract_dublin_core_metadata(source_record["html_base64"])

        for link in dc_meta.get("Identifier", []):
            if not link.lower().startswith("http"):
                continue
            links.append(timdex.Link(url=link))

        return links or None

    def get_fulltext(self, source_record: dict) -> str | None:
        """Extract meaningful full-text from full Libguide HTML.

        This does not currently capture sidebar content, where things like the guide
        creator or staff profile is populated.  This is a consideration for future work.

        This method also extracts text from "keywords" metadata tags (repeatable) and
        adds to the fulltext saved for the record.
        """
        html_soup = self.parse_html(source_record["html_base64"])

        # capture fulltext from guide content
        texts = set()
        selectors = [
            ("div", {"class": "s-lib-header"}),
            ("div", {"class": "s-lib-main"}),
        ]

        for element, attrs in selectors:
            if target := html_soup.find(element, attrs=attrs):
                texts.add(target.get_text(separator=" ", strip=True))

        # capture fulltext from any "keywords" metadata elements
        for meta in html_soup.find_all("meta"):
            name = meta.get("name")

            if not name or name.strip().lower() != "keywords":
                continue

            content = meta.get("content")
            if not content or not content.strip():
                continue

            texts.add(content)

        return "\n".join(texts)

    @classmethod
    def get_summary(cls, source_record: dict) -> list[str] | None:
        summaries = []
        dc_meta = cls.extract_dublin_core_metadata(source_record["html_base64"])

        for description in dc_meta.get("Description", []):
            summaries.append(description)  # noqa: PERF402

        return summaries or None

    @classmethod
    def get_publishers(cls, source_record: dict) -> list[timdex.Publisher] | None:
        dc_meta = cls.extract_dublin_core_metadata(source_record["html_base64"])
        return [
            timdex.Publisher(name=publisher)
            for publisher in dc_meta.get("Publishers", [])
        ] or None

    @classmethod
    def get_rights(cls, source_record: dict) -> list[timdex.Rights] | None:
        dc_meta = cls.extract_dublin_core_metadata(source_record["html_base64"])
        return [
            timdex.Rights(description=right) for right in dc_meta.get("Rights", [])
        ] or None

    @classmethod
    def get_subjects(cls, source_record: dict) -> list[timdex.Subject] | None:
        dc_meta = cls.extract_dublin_core_metadata(source_record["html_base64"])
        if subjects := dc_meta.get("Subject"):
            return [timdex.Subject(kind="Subject scheme not provided", value=subjects)]
        return None

    @classmethod
    def get_languages(cls, source_record: dict) -> list[str] | None:
        dc_meta = cls.extract_dublin_core_metadata(source_record["html_base64"])
        if languages := dc_meta.get("Language"):
            return languages
        return None
