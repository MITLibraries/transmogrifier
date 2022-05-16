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
def datacite_records():
    return parse_xml_records("tests/fixtures/datacite/datacite_records.xml")


@pytest.fixture()
def datacite_record_all_fields():
    return parse_xml_records("tests/fixtures/datacite/datacite_record_all_fields.xml")


@pytest.fixture()
def datacite_record_required_fields():
    return parse_xml_records(
        "tests/fixtures/datacite/datacite_record_required_fields.xml"
    )


@pytest.fixture()
def datacite_record_missing_required_fields_warning():
    return parse_xml_records(
        "tests/fixtures/datacite/datacite_record_missing_required_fields_warning.xml"
    )


@pytest.fixture()
def datacite_record_missing_required_field_error():
    return parse_xml_records(
        "tests/fixtures/datacite/datacite_record_missing_required_field_error.xml"
    )


@pytest.fixture()
def datacite_record_multiple_titles():
    return parse_xml_records(
        "tests/fixtures/datacite/datacite_record_multiple_titles.xml"
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
        source_link="https://example.com/123",
        timdex_record_id="cool-repo:123",
        title="Some Data About Trees",
    )


@pytest.fixture()
def timdex_record_all_fields_and_subfields():
    return TimdexRecord(
        citation="Creator (PubYear): Title. Publisher. (resourceTypeGeneral). ID",
        source="A Cool Repository",
        source_link="https://example.com/123",
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
                award_uri="http://awards.example/7689",
            )
        ],
        identifiers=[Identifier(value="123", kind="doi")],
        languages=["en_US"],
        locations=[
            Location(
                value="A point on the globe",
                kind="Data was gathered here",
                geodata=[-77.025955, 38.942142],
            )
        ],
        notes=[Note(value=["This book is awesome"], kind="opinion")],
        publication_information=["Version 1.0"],
        related_items=[
            RelatedItem(
                description="This item is related to this other item",
                item_type="An item type",
                relationship="isReferencedBy",
                uri="http://doi.example/123",
            )
        ],
        rights=[
            Rights(
                description="People may use this",
                kind="Access rights",
                uri="http://rights.example/",
            ),
        ],
        subjects=[Subject(value=["Stuff"], kind="LCSH")],
        summary=["This is data."],
    )


@pytest.fixture()
def zenodo_record():
    return parse_xml_records("tests/fixtures/datacite/zenodo_record.xml")
