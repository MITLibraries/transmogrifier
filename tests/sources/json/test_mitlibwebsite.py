# ruff: noqa: RUF001
from unittest.mock import MagicMock, patch

import transmogrifier.models as timdex
from transmogrifier.sources.json.mitlibwebsite import MITLibWebsite


def create_mitlibwebsite_source_record_stub() -> dict:
    return {
        "url": "https://libraries.mit.edu/search/",
        "cdx_title": "Search | MIT Libraries",
        "og_description": "Use this page to learn about different ways you can search the MIT Libraries' offerings.",  # noqa: E501
    }


def test_mitlibwebsite_transform_returns_timdex_record(mitlibwebsite_records):
    mitlibwebsite = MITLibWebsite("mitlibwebsite", mitlibwebsite_records)
    timdex_record = mitlibwebsite.transform(next(mitlibwebsite.source_records))
    assert timdex_record == timdex.TimdexRecord(
        source="MIT Libraries Website",
        source_link="https://libraries.mit.edu/search/",
        timdex_record_id="mitlibwebsite:d8c00768549a53c235de0493d05effa5",
        title="Search | MIT Libraries",
        citation="MIT Libraries. Search | MIT Libraries. Website. https://libraries.mit.edu/search/",
        content_type=["Website"],
        contributors=[
            timdex.Contributor(
                value="MIT Libraries",
                affiliation=None,
                identifier=None,
                kind="creator",
                mit_affiliated=True,
            )
        ],
        dates=[timdex.Date(value="2000-01-01T00:00:00", kind="Accessed")],
        format="electronic resource",
        links=[
            timdex.Link(
                url="https://libraries.mit.edu/search/",
                kind="Website",
                restrictions=None,
                text=None,
            )
        ],
        summary=[
            "Use this page to learn about different ways you can search the MIT Libraries’ offerings. Use the Default Quick Search Our Quick Search is the default search on the Libraries’ homepage. This collects results from different library search tools and sorts the results into 4 categories: Books and media Articles and book chapters Archives and manuscript collections Our library website and guides The tool will search the 4 categories and present the top results from each category. It is useful to see the full breadth of what MIT Libraries has on a particular topic or author. Go straight to our […]"  # noqa: E501
        ],
    )


def test_mitlibwebsite_record_get_main_titles_success():
    source_record = create_mitlibwebsite_source_record_stub()
    assert MITLibWebsite.get_main_titles(source_record) == ["Search | MIT Libraries"]


def test_mitlibwebsite_get_source_link_success():
    source_record = create_mitlibwebsite_source_record_stub()
    mitlibwebsite = MITLibWebsite("mitlibwebsite", iter([source_record]))
    assert (
        mitlibwebsite.get_source_link(source_record)
        == "https://libraries.mit.edu/search/"
    )


@patch("hashlib.md5")
def test_mitlibwebsite_get_timdex_record_id(mock_md5):
    mock_hash_obj = MagicMock()
    mock_hash_obj.hexdigest.return_value = "banana"
    mock_md5.return_value = mock_hash_obj

    source_record = create_mitlibwebsite_source_record_stub()
    mitlibwebsite = MITLibWebsite("mitlibwebsite", iter([source_record]))
    assert mitlibwebsite.get_timdex_record_id(source_record) == "mitlibwebsite:banana"


@patch("hashlib.md5")
def test_mitlibwebsite_get_source_record_id(mock_md5):
    mock_hash_obj = MagicMock()
    mock_hash_obj.hexdigest.return_value = "banana"
    mock_md5.return_value = mock_hash_obj

    source_record = create_mitlibwebsite_source_record_stub()
    assert MITLibWebsite.get_source_record_id(source_record) == "banana"


def test_mitlibwebsite_get_content_type_success():
    source_record = create_mitlibwebsite_source_record_stub()
    assert MITLibWebsite.get_content_type(source_record) == ["Website"]


def test_mitlibwebsite_get_contributors_success():
    source_record = create_mitlibwebsite_source_record_stub()
    assert MITLibWebsite.get_contributors(source_record) == [
        timdex.Contributor(value="MIT Libraries", kind="creator", mit_affiliated=True)
    ]


def test_mitlibwebsite_get_dates_success():
    source_record = create_mitlibwebsite_source_record_stub()
    mitlibwebsite = MITLibWebsite("mitlibwebsite", iter([source_record]))
    assert mitlibwebsite.get_dates(source_record) == [
        timdex.Date(value="2000-01-01T00:00:00", kind="Accessed")
    ]


def test_mitlibwebsite_get_format_success():
    source_record = create_mitlibwebsite_source_record_stub()
    mitlibwebsite = MITLibWebsite("mitlibwebsite", iter([source_record]))
    assert mitlibwebsite.get_format(source_record) == "electronic resource"


def test_mitlibwebsite_get_links_success():
    source_record = create_mitlibwebsite_source_record_stub()
    assert MITLibWebsite.get_links(source_record) == [
        timdex.Link(url="https://libraries.mit.edu/search/", kind="Website")
    ]


def test_mitlibwebsite_get_summary_success():
    source_record = create_mitlibwebsite_source_record_stub()
    assert MITLibWebsite.get_summary(source_record) == [
        "Use this page to learn about different ways you can search the MIT Libraries' offerings."  # noqa: E501
    ]


def test_mitlibwebsite_get_summary_returns_none_if_og_description_is_none():
    source_record = create_mitlibwebsite_source_record_stub()
    source_record["og_description"] = None
    assert MITLibWebsite.get_summary(source_record) is None


def test_mitlibwebsite_record_is_deleted_returns_true_when_status_is_deleted():
    source_record = create_mitlibwebsite_source_record_stub()
    source_record["status"] = "deleted"
    assert MITLibWebsite.record_is_deleted(source_record) is True


def test_mitlibwebsite_record_is_deleted_returns_false_when_status_is_not_deleted():
    source_record = create_mitlibwebsite_source_record_stub()
    source_record["status"] = "active"
    assert MITLibWebsite.record_is_deleted(source_record) is False


def test_mitlibwebsite_record_is_deleted_returns_false_when_status_field_is_missing():
    source_record = create_mitlibwebsite_source_record_stub()
    assert MITLibWebsite.record_is_deleted(source_record) is False
