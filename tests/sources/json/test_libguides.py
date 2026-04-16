# ruff: noqa: E501, PLC0415, PLR2004, S301, SLF001

import base64
from unittest.mock import MagicMock, PropertyMock, patch

import pandas as pd
import pytest

from transmogrifier import models


@pytest.fixture(autouse=True)
def _test_env_libguides():
    with (
        patch("transmogrifier.config.LIBGUIDES_CLIENT_ID", "123"),
        patch("transmogrifier.config.LIBGUIDES_API_TOKEN", "aaabbbdddccc"),
    ):
        yield


@pytest.fixture
def mocked_libguides_api_client_df_property():
    """Mock API Guides dataframe from LibGuidesAPIClient."""
    from transmogrifier.sources.json.libguides import LibGuidesAPIClient

    api_guides_df = pd.read_pickle("tests/fixtures/libguides/libguides_api_guides_df.pkl")

    with patch.object(
        LibGuidesAPIClient,
        "api_guides_df",
        new_callable=PropertyMock,
        return_value=api_guides_df,
    ):
        yield


@pytest.fixture
def libguides_records():
    from transmogrifier.sources.json.libguides import LibGuides

    return LibGuides.parse_source_file(
        "tests/fixtures/libguides/libguides-2026-02-20-full-extracted-records-to-index.jsonl"
    )


@pytest.fixture
def libguides_transformer(mocked_libguides_api_client_df_property, libguides_records):
    """Create LibGuides transformer."""
    from transmogrifier.sources.json.libguides import LibGuides

    return LibGuides(
        "libguides",
        libguides_records,
    )


def create_libguides_source_record_stub(
    html_filepath="tests/fixtures/libguides/libguide.html",
) -> dict:
    with open(html_filepath) as f:
        html_content = f.read()

    return {
        "url": "https://libguides.mit.edu/bizcat",
        "status": "active",
        "cdx_warc_filename": "rec-d3274de52d0c-libguides-20260205201423787-6.warc.gz",
        "cdx_title": "Analyst reports - Business Databases by Category - LibGuides at MIT Libraries",
        "cdx_offset": "1001127",
        "cdx_length": "16655",
        "html_base64": base64.b64encode(html_content.encode()).decode(),
        "response_headers": {
            "Content-Security-Policy": ["upgrade-insecure-requests"],
            "content-type": ["text/html; charset=UTF-8"],
            "date": ["Thu, 05 Feb 2026 20:16:24 GMT"],
            "server": ["nginx"],
            "strict-transport-security": ["max-age=31536000; preload"],
            "vary": ["Accept-Encoding"],
            "x-backend-server": ["libguides-us-1.springyaws.com"],
            "x-content-type-options": ["nosniff"],
            "x-springy-cache-disabled": ["0"],
            "x-orig-content-encoding": ["gzip"],
        },
    }


def test_libguides_api_client_composition_and_guides_dataframe(libguides_transformer):
    """Test that LibGuides transformer has proper API client composition."""
    from transmogrifier.sources.json.libguides import LibGuidesAPIClient

    # assert composition to Transformer
    assert isinstance(libguides_transformer.api_client, LibGuidesAPIClient)

    # assert dataframe properties
    api_guides_df = libguides_transformer.api_client.api_guides_df
    assert isinstance(api_guides_df, pd.DataFrame)
    assert set(api_guides_df.columns) == {
        "count_hit",
        "created",
        "description",
        "friendly_url",
        "group_id",
        "id",
        "name",
        "nav_type",
        "owner_id",
        "published",
        "redirect_url",
        "site_id",
        "slug",
        "slug_id",
        "status",
        "status_label",
        "thumbnail_url",
        "type_id",
        "type_label",
        "updated",
        "url",
    }


def test_libguides_class_methods_can_utilize_api_client(
    mocked_libguides_api_client_df_property,
):
    from transmogrifier.sources.json.libguides import LibGuides

    source_record = create_libguides_source_record_stub()
    source_link = LibGuides.get_source_link(source_record)
    source_record_id = LibGuides.get_source_record_id(source_record)

    assert source_link == "https://libguides.mit.edu/bizcat"
    assert source_record_id == "guides-383403"


def test_libguides_api_client_single_api_call_for_guides_dataframe():
    """Using api_guides_df multiple times only makes one API call, rest are cached."""
    from transmogrifier.sources.json.libguides import LibGuidesAPIClient

    api_guides_df = pd.read_pickle("tests/fixtures/libguides/libguides_api_guides_df.pkl")
    client = LibGuidesAPIClient()

    with (
        patch.object(client, "fetch_guides", return_value=api_guides_df) as mock_fetch,
        patch.object(client, "get_api_token", return_value="fake-token"),
    ):
        _ = client.api_guides_df
        _ = client.api_guides_df
        _ = client.api_guides_df

    mock_fetch.assert_called_once()


def test_libguides_extract_dc_metadata_skips_empty_content():
    from transmogrifier.sources.json.libguides import LibGuides

    # reuses fixture which has a whitespace-only DC.Subject
    source_record = create_libguides_source_record_stub(
        html_filepath="tests/fixtures/libguides/libguide_non_url_identifier.html"
    )
    dc = LibGuides.extract_dublin_core_metadata(source_record["html_base64"])
    assert "Subject" not in dc


def test_libguides_record_get_main_titles_success(libguides_transformer):
    source_record = create_libguides_source_record_stub()
    assert libguides_transformer.get_main_titles(source_record) == [
        "Business Databases by Category: Analyst reports"
    ]


def test_libguides_record_get_main_titles_fallback_to_cdx_title(libguides_transformer):
    source_record = create_libguides_source_record_stub(
        html_filepath="tests/fixtures/libguides/libguide_minimal_dc.html"
    )
    assert libguides_transformer.get_main_titles(source_record) == [
        "Analyst reports - Business Databases by Category"
    ]


def test_libguides_record_is_deleted_success(libguides_transformer):
    source_record = create_libguides_source_record_stub()
    assert not libguides_transformer.record_is_deleted(source_record)

    source_record["status"] = "deleted"
    assert libguides_transformer.record_is_deleted(source_record)


def test_libguides_record_get_content_type_success(libguides_transformer):
    source_record = create_libguides_source_record_stub()
    assert libguides_transformer.get_content_type(source_record) == ["LibGuide"]


def test_libguides_record_get_dates_success(libguides_transformer):
    source_record = create_libguides_source_record_stub()
    dates = libguides_transformer.get_dates(source_record)
    assert set(dates) == {
        models.Date(kind="Accessed", note=None, range=None, value="2000-01-01"),
        models.Date(kind="Created", note=None, range=None, value="2015-09-13"),
        models.Date(kind="Modified", note=None, range=None, value="2026-02-02"),
    }


def test_libguides_record_get_format_success(libguides_transformer):
    source_record = create_libguides_source_record_stub()
    assert libguides_transformer.get_format(source_record) == "electronic resource"


def test_libguides_record_get_timdex_record_id(libguides_transformer):
    source_record = create_libguides_source_record_stub()
    assert (
        libguides_transformer.get_timdex_record_id(source_record)
        == "libguides:guides-383403"
    )


def test_libguides_record_get_identifiers_success(libguides_transformer):
    source_record = create_libguides_source_record_stub()
    identifiers = libguides_transformer.get_identifiers(source_record)
    assert identifiers == [models.Identifier(value="383403", kind="LibGuide ID")]


def test_libguides_record_get_identifiers_includes_non_url_dc_identifier(
    libguides_transformer,
):
    source_record = create_libguides_source_record_stub(
        html_filepath="tests/fixtures/libguides/libguide_non_url_identifier.html"
    )
    identifiers = libguides_transformer.get_identifiers(source_record)
    assert models.Identifier(value="ISBN:1234567890") in identifiers


def test_libguides_record_get_links_success(libguides_transformer):
    source_record = create_libguides_source_record_stub()
    links = libguides_transformer.get_links(source_record)
    assert links == [
        models.Link(
            url="https://libguides.mit.edu/bizcat/analysts",
            kind=None,
            restrictions=None,
            text=None,
        )
    ]


def test_libguides_record_get_links_returns_none_when_no_url_identifiers(
    libguides_transformer,
):
    source_record = create_libguides_source_record_stub(
        html_filepath="tests/fixtures/libguides/libguide_non_url_identifier.html"
    )
    assert libguides_transformer.get_links(source_record) is None


def test_libguides_record_get_fulltext_success(libguides_transformer):
    source_record = create_libguides_source_record_stub()
    fulltext = libguides_transformer.get_fulltext(source_record)

    assert "I am the main content." in fulltext
    assert "I am header information." in fulltext

    assert "You should not find me." not in fulltext
    assert "You should not find me either." not in fulltext


def test_libguides_record_get_fulltext_includes_keywords_metadata(
    libguides_transformer,
):
    html_content = """
    <html>
        <head>
            <meta name="keywords" content="alpha, beta"/>
            <meta name="keywords" content="   "/>
        </head>
        <body>
            <div class="s-lib-main"><p>Content</p></div>
        </body>
    </html>
    """
    source_record = create_libguides_source_record_stub()
    source_record["html_base64"] = base64.b64encode(html_content.encode()).decode()

    fulltext = libguides_transformer.get_fulltext(source_record)

    assert set(fulltext.splitlines()) == {"Content", "alpha, beta"}


def test_libguides_record_get_summary_success(libguides_transformer):
    source_record = create_libguides_source_record_stub()
    summary = libguides_transformer.get_summary(source_record)
    assert summary == ["This is a libguide about business databases."]


def test_libguides_record_get_publishers_success(libguides_transformer):
    source_record = create_libguides_source_record_stub()
    publishers = libguides_transformer.get_publishers(source_record)
    assert publishers == [
        models.Publisher(name="MIT Libraries", date=None, location=None)
    ]


def test_libguides_record_get_rights_success(libguides_transformer):
    source_record = create_libguides_source_record_stub()
    rights = libguides_transformer.get_rights(source_record)
    assert rights == [
        models.Rights(description="Copyright MIT Libraries 2026", kind=None, uri=None)
    ]


def test_libguides_record_get_subjects_success(libguides_transformer):
    source_record = create_libguides_source_record_stub()
    subjects = libguides_transformer.get_subjects(source_record)
    assert subjects == [
        models.Subject(
            value=["Business", "Databases"],
            kind="Subject scheme not provided",
        )
    ]


def test_libguides_record_get_subjects_returns_none_when_no_subjects(
    libguides_transformer,
):
    source_record = create_libguides_source_record_stub(
        html_filepath="tests/fixtures/libguides/libguide_minimal_dc.html"
    )
    assert libguides_transformer.get_subjects(source_record) is None


def test_libguides_record_get_languages_success(libguides_transformer):
    source_record = create_libguides_source_record_stub()
    languages = libguides_transformer.get_languages(source_record)
    assert languages == ["en"]


def test_libguides_record_get_languages_returns_none_when_no_languages(
    libguides_transformer,
):
    source_record = create_libguides_source_record_stub(
        html_filepath="tests/fixtures/libguides/libguide_minimal_dc.html"
    )
    assert libguides_transformer.get_languages(source_record) is None


def test_libguides_record_is_excluded_when_guide_in_excluded_group(libguides_transformer):
    source_record = create_libguides_source_record_stub()
    url = source_record["url"]

    # modify the LibGuides API dataframe to put this guide in an excluded group
    # this works because libguides_transformer.api_client.api_guides_df is a cached
    # object that gets reused, so it's modifiable like this
    df = libguides_transformer.api_client.api_guides_df
    df.loc[df.friendly_url == url, "group_id"] = 3754
    libguides_transformer._allowed_guides_df = None

    assert libguides_transformer.record_is_excluded(source_record)


def test_libguides_record_is_excluded_when_guide_type_not_allowed(libguides_transformer):
    source_record = create_libguides_source_record_stub()
    url = source_record["url"]

    # modify the LibGuides API dataframe to give this guide a non-allowed type
    # this works because libguides_transformer.api_client.api_guides_df is a cached
    # object that gets reused, so it's modifiable like this
    df = libguides_transformer.api_client.api_guides_df
    df.loc[df.friendly_url == url, "type_label"] = "Internal Guide"
    libguides_transformer._allowed_guides_df = None

    assert libguides_transformer.record_is_excluded(source_record)


def test_libguides_api_client_fetch_guides_expands_sub_pages_into_rows():
    """Test that sub-pages from the API are expanded into their own DataFrame rows.

    Sub-pages inherit parent guide columns (like type_label, status_label, group_id)
    so they are treated identically to root pages throughout the transformation pipeline.
    """
    from transmogrifier.sources.json.libguides import LibGuidesAPIClient

    mock_api_response = [
        {
            "id": 100,
            "name": "Root Guide",
            "url": "https://libguides.mit.edu/c.php?g=100",
            "friendly_url": "https://libguides.mit.edu/rootguide",
            "type_label": "General Purpose Guide",
            "status_label": "Published",
            "group_id": 0,
            "pages": [
                {
                    "id": 200,
                    "name": "Sub Page",
                    "url": "https://libguides.mit.edu/c.php?g=100&p=200",
                    "friendly_url": None,
                }
            ],
        }
    ]

    client = LibGuidesAPIClient()
    mock_response = MagicMock()
    mock_response.json.return_value = mock_api_response

    with patch(
        "transmogrifier.sources.json.libguides.requests.get",
        return_value=mock_response,
    ):
        df = client.fetch_guides("fake-token")

    # 1 guide + 1 sub-page = 2 rows
    assert len(df) == 2

    # root page untouched
    root_row = df[df["id"] == 100].iloc[0]
    assert root_row["url"] == "https://libguides.mit.edu/c.php?g=100"
    assert root_row["friendly_url"] == "https://libguides.mit.edu/rootguide"

    # sub-page has its own row
    sub_row = df[df["id"] == 200].iloc[0]
    assert sub_row["url"] == "https://libguides.mit.edu/c.php?g=100&p=200"
    assert sub_row["friendly_url"] is None

    # sub-page inherits parent types and statuses
    assert sub_row["type_label"] == "General Purpose Guide"
    assert sub_row["status_label"] == "Published"
    assert sub_row["group_id"] == 0
