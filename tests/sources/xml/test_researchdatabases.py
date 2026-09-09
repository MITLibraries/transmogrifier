# ruff: noqa: PLR2004, SLF001

from unittest.mock import patch

import pytest
from bs4 import Tag

from transmogrifier.exceptions import CriticalError
from transmogrifier.helpers import LibGuidesAPIClient
from transmogrifier.sources.xml.researchdatabases import (
    ResearchDatabases,
)


@pytest.fixture(autouse=True)
def _test_env_libguides():
    with (
        patch("transmogrifier.config.LIBGUIDES_CLIENT_ID", "123"),
        patch("transmogrifier.config.LIBGUIDES_API_TOKEN", "aaabbbdddccc"),
        patch("transmogrifier.config.TIMDEX_DATASET_LOCATION", "s3://timdex/dataset"),
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
def mocked_timdex_dataset_az_identifiers():
    with patch.object(
        ResearchDatabases,
        "_get_current_dataset_az_identifiers",
        return_value=[
            "1234",  # mocked as present only in dataset, not current/public
            "7777",
            "8888",
            "9999",
        ],
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
    mocked_timdex_dataset_az_identifiers,
    mocked_current_az_identifiers,
):
    deleted_records = list(
        researchdatabases_transformer._yield_api_records_for_deleting()
    )
    assert len(deleted_records) == 1
    assert isinstance(deleted_records[0], Tag)


def test_researchdatabases_synthetic_deleted_record(
    researchdatabases_transformer,
    mocked_timdex_dataset_az_identifiers,
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


@pytest.mark.parametrize(
    "env_var",
    [
        "LIBGUIDES_API_TOKEN",
        "LIBGUIDES_CLIENT_ID",
        "TIMDEX_DATASET_LOCATION",
    ],
)
def test_researchdatabases_env_vars_not_set_skips_deletes(
    env_var,
    caplog,
    researchdatabases_transformer,
    mocked_current_az_identifiers,
):
    caplog.set_level("WARNING")
    with patch(f"transmogrifier.config.{env_var}", None):
        assert list(researchdatabases_transformer._yield_api_records_for_deleting()) == []

    assert (
        "Skipping deleting record detection, not all required env vars are set."
        in caplog.text
    )


def test_researchdatabases_deletion_ratio_under_threshold_passes(
    researchdatabases_transformer,
    mocked_timdex_dataset_az_identifiers,
    mocked_current_az_identifiers,
):
    """A deletion ratio under DELETION_COUNT_THRESHOLD yields delete records."""
    deleted_records = list(
        researchdatabases_transformer._yield_api_records_for_deleting()
    )
    assert len(deleted_records) == 1
    assert isinstance(deleted_records[0], Tag)


def test_researchdatabases_deletion_ratio_over_threshold_raises(
    researchdatabases_transformer,
    mocked_current_az_identifiers,
):
    """A deletion ratio exceeding DELETION_COUNT_THRESHOLD raises CriticalError."""
    # all dataset records marked for delete -> 100% ratio
    with (
        patch.object(
            ResearchDatabases,
            "_get_current_dataset_az_identifiers",
            return_value=["1234", "7777", "8888", "9999"],
        ),
        patch.object(
            LibGuidesAPIClient,
            "get_current_az_identifiers",
            return_value=[],
        ),
        pytest.raises(CriticalError) as excinfo,
    ):
        list(researchdatabases_transformer._yield_api_records_for_deleting())

    assert "exceeds the deletion percentage threshold" in str(excinfo.value)


def test_researchdatabases_empty_dataset_identifiers_passes(
    researchdatabases_transformer,
    mocked_current_az_identifiers,
):
    """An empty dataset identifier list skips the threshold check entirely."""
    with patch.object(
        ResearchDatabases,
        "_get_current_dataset_az_identifiers",
        return_value=[],
    ):
        deleted_records = list(
            researchdatabases_transformer._yield_api_records_for_deleting()
        )

    assert deleted_records == []


def test_research_databases_custom_parse_source_file_yields_oai_and_synthetic_records(
    researchdatabases_transformer,
    mocked_timdex_dataset_az_identifiers,
    mocked_current_az_identifiers,
):
    records = list(researchdatabases_transformer.source_records)

    assert len(records) == 4  # 3 OAI + 1 synthetic delete
