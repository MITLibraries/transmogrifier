import pytest
from click.testing import CliRunner

from transmogrifier.helpers import parse_xml_records
from transmogrifier.models import TimdexRecord
from transmogrifier.sources.datacite import Datacite


@pytest.fixture()
def runner():
    return CliRunner()


@pytest.fixture()
def datacite_jpal_records():
    return parse_xml_records("tests/fixtures/datacite_jpal_records.xml")


@pytest.fixture()
def datacite_jpal_record_full():
    return parse_xml_records("tests/fixtures/datacite_jpal_record_full.xml")


@pytest.fixture()
def datacite_jpal_record_minimal():
    return parse_xml_records("tests/fixtures/datacite_jpal_record_minimal.xml")


@pytest.fixture()
def datacite_jpal_record_missing_required_field():
    return parse_xml_records(
        "tests/fixtures/datacite_jpal_record_missing_required_field.xml"
    )


@pytest.fixture()
def datacite_jpal_record_multiple_titles():
    return parse_xml_records("tests/fixtures/datacite_jpal_record_multiple_titles.xml")


@pytest.fixture()
def datacite_jpal_record_orcid_name_identifier():
    return parse_xml_records(
        "tests/fixtures/datacite_jpal_record_orcid_name_identifier.xml"
    )


@pytest.fixture()
def datacite_jpal_record_unknown_name_identifier():
    return parse_xml_records(
        "tests/fixtures/datacite_jpal_record_unknown_name_identifier.xml"
    )


@pytest.fixture()
def datacite_record():
    return Datacite(
        source_symbol="cool",
        source_name="A Cool Repository",
        source_base_url="https://example.com/item123",
        input_records=None,
    )


@pytest.fixture()
def timdex_record():
    return TimdexRecord(
        source="A Cool Repository",
        source_link="https://example.com/item123",
        timdex_record_id="cool-repo:123",
        title="Some Data About Trees",
    )
