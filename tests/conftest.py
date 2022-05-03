from functools import partial

import pytest
from click.testing import CliRunner

from transmogrifier.helpers import parse_xml_records
from transmogrifier.models import (
    AlternateTitle,
    Contributor,
    Date,
    Date_Range,
    Funder,
    Identifier,
    Location,
    Note,
    RelatedItem,
    Rights,
    Subject,
    TimdexRecord,
)
from transmogrifier.sources.datacite import Datacite


@pytest.fixture()
def runner():
    return CliRunner()


@pytest.fixture()
def datacite_jpal_records():
    return parse_xml_records("tests/fixtures/datacite/jpal_records.xml")


@pytest.fixture()
def datacite_jpal_record_all_fields():
    return parse_xml_records("tests/fixtures/datacite/jpal_record_all_fields.xml")


@pytest.fixture()
def datacite_jpal_record_required_fields():
    return parse_xml_records("tests/fixtures/datacite/jpal_record_required_fields.xml")


@pytest.fixture()
def datacite_jpal_record_missing_required_field():
    return parse_xml_records(
        "tests/fixtures/datacite/jpal_record_missing_required_field.xml"
    )


@pytest.fixture()
def datacite_jpal_record_multiple_titles():
    return parse_xml_records("tests/fixtures/datacite/jpal_record_multiple_titles.xml")


@pytest.fixture()
def datacite_jpal_record_orcid_name_identifier():
    return parse_xml_records(
        "tests/fixtures/datacite/jpal_record_orcid_name_identifier.xml"
    )


@pytest.fixture()
def datacite_jpal_record_unknown_name_identifier():
    return parse_xml_records(
        "tests/fixtures/datacite/jpal_record_unknown_name_identifier.xml"
    )


@pytest.fixture()
def datacite_record_partial():
    return partial(
        Datacite,
        source="cool-repo",
        source_name="A Cool Repository",
        source_base_url="https://example.com/",
    )


@pytest.fixture()
def timdex_record_required_fields():
    return TimdexRecord(
        source="A Cool Repository",
        source_link="https://example.com/",
        timdex_record_id="cool-repo:123",
        title="Some Data About Trees",
    )


@pytest.fixture()
def timdex_record_all_fields_and_subfields():
    return TimdexRecord(
        source="A Cool Repository",
        source_link="https://example.com/",
        timdex_record_id="cool-repo:123",
        title="Some Data About Trees",
        alternate_titles=[AlternateTitle(value="Alt title", kind="alternative")],
        content_type=["dataset"],
        contributors=[
            Contributor(
                value="Smith, Jane",
                affiliation=["MIT"],
                identifier=["https://orcid.org/456"],
                kind="author",
                mit_affiliated=True,
            ),
        ],
        dates=[
            Date(kind="date of publication", value="2020-01-15"),
            Date(
                kind="dates collected",
                note="data collected every 3 days",
                range=Date_Range(gt="2019-01-01", lt="2019-06-30"),
            ),
        ],
        edition="2nd revision",
        file_formats=["application/pdf"],
        format="electronic resource",
        funding_information=[
            Funder(
                funder_name="Funding Foundation",
                funder_identifier="4356",
                funder_identifier_type="Crossref FunderID",
                award_number="3124",
                award_uri="http://awards.example/",
            )
        ],
        identifiers=[Identifier(value="123", kind="doi")],
        languages=["en_US"],
        locations=[Location(value="Data gathered at a place")],
        notes=[Note(value="This book is awesome", kind="opinion")],
        publication_information=["Version 1.0"],
        related_items=[
            RelatedItem(uri="http://doi.example/123", kind="isReferencedBy")
        ],
        rights=[
            Rights(description="People may use this", uri="http://rights.example/"),
        ],
        subjects=[Subject(value="Stuff", kind="LCSH")],
        summary=["This is data."],
    )
