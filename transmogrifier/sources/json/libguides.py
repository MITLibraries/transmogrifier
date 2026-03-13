import base64
import logging
import re
from collections import defaultdict
from functools import lru_cache
from urllib.parse import urlparse

import pandas as pd
import requests
from bs4 import BeautifulSoup, Tag
from dateutil.parser import parse as date_parser

import transmogrifier.models as timdex
from transmogrifier.config import (
    LIBGUIDES_API_TOKEN,
    LIBGUIDES_CLIENT_ID,
    LIBGUIDES_GUIDES_URL,
    LIBGUIDES_TOKEN_URL,
)
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


class LibGuidesAPIClient:
    """Client for LibGuides API communication and data retrieval.

    This class retrieves metadata about all LibGuides via an API, retrieving data that is
    not found in the OAI-PMH XML records or the websites themselves.  This valuable data
    is used during transformation to identify records for exclusion, occasionally
    provide friendlier URLs, and other data augmentation.

    This class is instantiated as a singleton object in this module.  Once instantiated,
    it is attached to the Libguides transformer instance.  This allows class methods
    on the transformer to access cached data from this singleton object, ultimately
    resulting in only a single API call per multiple record transformation run.

    This class relies on two environment variables:
        - LIBGUIDES_CLIENT_ID
        - LIBGUIDES_API_TOKEN
    """

    def __init__(self) -> None:
        if not LIBGUIDES_CLIENT_ID:
            raise RuntimeError("Required env var 'LIBGUIDES_CLIENT_ID' is not set")
        if not LIBGUIDES_API_TOKEN:
            raise RuntimeError("Required env var 'LIBGUIDES_API_TOKEN' is not set")

        self.client_id = str(LIBGUIDES_CLIENT_ID)
        self.client_secret = LIBGUIDES_API_TOKEN
        self._api_guides_df: pd.DataFrame | None = None

    @property
    def api_guides_df(self) -> pd.DataFrame:
        if self._api_guides_df is None:
            self._api_guides_df = self.fetch_guides(self.get_api_token())
        return self._api_guides_df

    def get_api_token(self) -> str:
        data = {
            "grant_type": "client_credentials",
            "client_id": self.client_id,
            "client_secret": self.client_secret,
        }
        response = requests.post(LIBGUIDES_TOKEN_URL, headers={}, data=data, timeout=60)
        response.raise_for_status()
        payload = response.json()
        return payload.get("access_token")

    def fetch_guides(self, token: str) -> pd.DataFrame:
        """Retrieve metadata for all LibGuides.

        Each guide may contain a 'pages' key with a list of sub-page dicts.  These
        sub-pages are expanded into their own rows in the returned DataFrame, inheriting
        any columns from the parent guide that the sub-page does not have.
        """
        logger.debug("Retrieving all guides from Libguides API.")
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(LIBGUIDES_GUIDES_URL, headers=headers, timeout=60)
        response.raise_for_status()
        guides = response.json()

        all_rows: list[dict] = []
        for guide in guides:
            pages = guide.get("pages", [])
            all_rows.append(guide)
            for page in pages:
                # inherit parent columns, then overlay page-specific columns
                page_row = {**guide, **page}
                all_rows.append(page_row)

        return pd.DataFrame(all_rows)

    def get_guide_by_url(self, url: str) -> pd.Series:
        """Get metadata for a single guide via a URL."""
        # strip GET parameter preview=...; duplicate for base URL
        url = re.sub(r"&preview=[^&]*", "", url)

        matches = self.api_guides_df[
            (self.api_guides_df.url == url) | (self.api_guides_df.friendly_url == url)
        ]
        if len(matches) == 1:
            return matches.iloc[0]

        raise ValueError(f"Found {len(matches)} guide ids for URL: {url}, expecting one.")


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
        guide = cls.api_client.get_guide_by_url(url)
        friendly_url = guide.get("friendly_url") or ""
        return friendly_url.strip() or url

    @classmethod
    def get_source_record_id(cls, source_record: dict) -> str:
        """Use numeric 'id' field from Libguides metadata with 'guides-' prefix."""
        guide = cls.api_client.get_guide_by_url(cls.get_source_link(source_record))
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

        Note: this does not currently capture sidebar content, where things like the guide
        creator or staff profile is populated.  This is a consideration for future work.
        """
        html_soup = self.parse_html(source_record["html_base64"])

        texts = set()
        selectors = [
            ("div", {"class": "s-lib-header"}),
            ("div", {"class": "s-lib-main"}),
        ]

        for element, attrs in selectors:
            if target := html_soup.find(element, attrs=attrs):
                texts.add(target.get_text(separator=" ", strip=True))

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
