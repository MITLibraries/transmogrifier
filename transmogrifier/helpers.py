import logging
import re
from datetime import UTC, datetime

import pandas as pd
import requests

import transmogrifier.models as timdex
from transmogrifier import config
from transmogrifier.config import DATE_FORMATS

logger = logging.getLogger(__name__)


def generate_citation(timdex_record: timdex.TimdexRecord) -> str:
    """Generate a citation in the Datacite schema format.

    timdex_record: A TimdexRecord instance from which to generate a citation.
    """
    citation = ""
    title = timdex_record.title
    url_string = f" {timdex_record.source_link}"

    creator_string = ""
    if timdex_record.contributors:
        creator_names = [
            contributor.value
            for contributor in timdex_record.contributors
            if (contributor.kind and contributor.kind.lower() == "author")
            or (contributor.kind and contributor.kind.lower() == "creator")
        ]
        creator_string = (", ").join(creator_names)

    publication_dates = ""
    if dates := timdex_record.dates:
        publication_dates = [  # type: ignore[assignment]
            date.value for date in dates if date.kind == "Publication date" and date.value
        ]

    if creator_string and publication_dates:
        citation += f"{creator_string} ({publication_dates[0]}): {title}."
    elif creator_string and not publication_dates:
        citation += f"{creator_string.rstrip('.')}. {title}."
    elif publication_dates and not creator_string:
        citation += f"{title}. {publication_dates[0]}."
    else:
        citation += f"{title}."

    publisher_string = ""
    if publishers_field := timdex_record.publishers:
        if publisher_location := publishers_field[0].location:
            publisher_string = f" {publisher_location} :"
        if publisher_name := publishers_field[0].name:
            publisher_string += f" {publisher_name}."

    resource_types = timdex_record.content_type
    resource_type_string = f" {(', ').join(resource_types)}." if resource_types else ""

    citation += publisher_string + resource_type_string + url_string
    return citation


def parse_date_from_string(
    date_string: str,
) -> datetime | None:
    """
    Transform a date string into a datetime object according to one of the configured
    OpenSearch date formats. Returns None if the date string cannot be parsed.

    Args:
        date_string: A date string.
    """
    for date_format in DATE_FORMATS:
        try:
            return datetime.strptime(date_string, date_format).astimezone(UTC)
        except ValueError:
            pass
    return None


def validate_date(
    date_string: str,
    source_record_id: str,
) -> bool:
    """
    Validate that a date string can be parsed according to one of the configured
    OpenSearch date formats. Returns True if date string is valid or returns
    False and logs an error.

    Args:
        date_string: A date string.
        source_record_id: The ID of the record being transformed.
    """
    if parse_date_from_string(date_string):
        return True
    logger.debug(
        "Record ID '%s' has a date that couldn't be parsed: '%s'",
        source_record_id,
        date_string,
    )
    return False


def validate_date_range(
    start_date: str,
    end_date: str,
    source_record_id: str,
) -> bool:
    """
    Validate a date range by validating that the start and end dates can be parsed and
    ensuring that the start date is before the end date to avoid an OpenSearch exception.
    Returns true if only one date exists in the range or the end date is after the start
    date, otherwise returns False and logs an error.

    Args:
        start_date: The start date of a date range.
        end_date: The end date of a date range.
        source_record_id: The ID of the record being transformed.
    """
    start_date_object = parse_date_from_string(start_date)
    end_date_object = parse_date_from_string(end_date)
    if start_date_object and end_date_object:
        if start_date_object <= end_date_object:
            return True
        logger.debug(
            "Record ID '%s' has a later start date than end date: '%s', '%s'",
            source_record_id,
            start_date,
            end_date,
        )
        return False
    logger.debug(
        "Record ID '%s' has invalid values in a date range: '%s', '%s'",
        source_record_id,
        start_date,
        end_date,
    )
    return False


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
        if not config.LIBGUIDES_CLIENT_ID:
            raise RuntimeError("Required env var 'LIBGUIDES_CLIENT_ID' is not set")
        if not config.LIBGUIDES_API_TOKEN:
            raise RuntimeError("Required env var 'LIBGUIDES_API_TOKEN' is not set")

        self.client_id = str(config.LIBGUIDES_CLIENT_ID)
        self.client_secret = config.LIBGUIDES_API_TOKEN
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
        response = requests.post(
            config.LIBGUIDES_TOKEN_URL, headers={}, data=data, timeout=60
        )
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
        response = requests.get(config.LIBGUIDES_GUIDES_URL, headers=headers, timeout=60)
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
        url = re.sub(r"([&?])preview=.*", "", url)
        url = url.removesuffix("/")

        matches = self.api_guides_df[
            (self.api_guides_df.url.str.lower() == url.lower())
            | (self.api_guides_df.friendly_url.str.lower() == url.lower())
        ]
        if len(matches) == 1:
            return matches.iloc[0]

        raise ValueError(f"Found {len(matches)} guide ids for URL: {url}, expecting one.")

    def fetch_az(self, token: str) -> pd.DataFrame:
        """Retrieve AZ items from API."""
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(
            "https://lgapi-us.libapps.com/1.2/az?expand=pages",
            headers=headers,
            timeout=60,
        )
        response.raise_for_status()
        return pd.DataFrame(response.json())

    def get_current_az_identifiers(self) -> list[str]:
        """Get list of identifiers for non-hidden / public AZ items.

        When filtering to enable_hidden = 0, the count matches the OAI-PMH full harvest
        for AZ items.
        """
        az_df = self.fetch_az(self.get_api_token())
        non_hidden_az_df = az_df[az_df.enable_hidden == "0"]
        return list(non_hidden_az_df.id)
