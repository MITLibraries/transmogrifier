# ruff: noqa: PLR2004, SLF001

from unittest.mock import patch

import pytest
from bs4 import Tag

from transmogrifier.helpers import LibGuidesAPIClient
from transmogrifier.sources.xml.researchdatabases import ResearchDatabases


@pytest.fixture
def last_az_identifiers(tmp_path) -> str:
    path = tmp_path / "last_az_identifiers.txt"
    with open(path, "w") as f:
        f.write("1234")
    return str(path)


@pytest.fixture(autouse=True)
def _test_env_libguides(last_az_identifiers):
    with (
        patch("transmogrifier.config.LIBGUIDES_CLIENT_ID", "123"),
        patch("transmogrifier.config.LIBGUIDES_API_TOKEN", "aaabbbdddccc"),
        patch(
            "transmogrifier.sources.xml.researchdatabases.LAST_AZ_IDENTIFIERS_PATH",
            last_az_identifiers,
        ),
    ):
        yield


@pytest.fixture
def mocked_current_az_identifiers():
    """Mock current AZ identifiers from LibGuides API, none matching previous ones."""
    with patch.object(
        LibGuidesAPIClient,
        "get_current_az_identifiers",
        return_value=["7777", "8888", "9999"],
    ):
        yield


@pytest.fixture
def researchdatabases_transformer():

    return ResearchDatabases.load(
        "researchdatabases",
        (
            "tests/fixtures/researchdatabases/researchdatabases-"
            "2026-08-11-full-extracted-records-to-index.xml"
        ),
    )


def test_researchdatabases_yields_oai_records_pass(researchdatabases_transformer):

    oai_records = list(
        researchdatabases_transformer._yield_oai_xml_records_for_indexing(
            researchdatabases_transformer.source_file
        )
    )

    assert len(oai_records) == 3
    assert isinstance(oai_records[0], Tag)


def test_researchdatabases_yields_deleted_records_success(
    researchdatabases_transformer,
    mocked_current_az_identifiers,
):
    deleted_records = list(
        researchdatabases_transformer._yield_api_records_for_deleting()
    )
    assert len(deleted_records) == 1
    assert isinstance(deleted_records[0], Tag)


def test_researchdatabases_synthetic_deleted_record(
    researchdatabases_transformer,
    mocked_current_az_identifiers,
):
    """Assert that Transformer injects synthetic OAI delete records.

    Example record:

    <?xml version="1.0" encoding="utf-8"?>
    <record>
        <header status="deleted">
            <identifier>oai:libguides.com:az/1234</identifier>
            <datestamp>2026-08-11T14:13:38Z</datestamp>
            <setSpec>az</setSpec>
        </header>
        <note>This is a synthetic delete record created by Transmogrifier.</note>
        <metadata/>
    </record>
    """
    deleted_record = next(researchdatabases_transformer._yield_api_records_for_deleting())

    header = deleted_record.find("record").find("header")

    assert header.get("status") == "deleted"
    assert header.find("identifier").string == "oai:libguides.com:az/1234"
    assert (
        deleted_record.find("note").string
        == "This is a synthetic delete record created by Transmogrifier."
    )


def test_researchdatabases_last_az_identifiers_file_updated(
    researchdatabases_transformer, mocked_current_az_identifiers, last_az_identifiers
):
    """Assert the last AZ identifiers list is updated."""
    _ = list(researchdatabases_transformer._yield_api_records_for_deleting())
    with open(last_az_identifiers) as f:
        assert f.read() == """7777\n8888\n9999\n"""


def test_researchdatabases_identifiers_text_file_missing_error(
    tmp_path,
    researchdatabases_transformer,
    mocked_current_az_identifiers,
):
    """Assert that missing AZ identifiers list will bubble up exception."""
    bad_path = tmp_path / "does-not-exist.txt"
    with (
        patch(
            "transmogrifier.sources.xml.researchdatabases.LAST_AZ_IDENTIFIERS_PATH",
            bad_path,
        ),
        pytest.raises(FileNotFoundError, match=r"does-not-exist.txt"),
    ):
        list(researchdatabases_transformer._yield_api_records_for_deleting())


def test_research_databases_custom_parse_source_file_yields_oai_and_synthetic_records(
    researchdatabases_transformer,
    mocked_current_az_identifiers,
):
    records = list(researchdatabases_transformer.source_records)

    assert len(records) == 4  # 3 OAI + 1 synthetic delete
