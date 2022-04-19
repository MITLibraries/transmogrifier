import json

import pytest
from click.testing import CliRunner
from defusedxml import ElementTree as ET


@pytest.fixture()
def runner():
    return CliRunner()


@pytest.fixture()
def timdex_record_generic_full():
    return {
        "timdex_record_id": "123",
        "title": "Dataset 1",
        "identifiers": [{"value": "123", "kind": "DOI"}],
        "source": "Data Provider",
        "source_link": "example://example.example",
        "contributors": [
            {
                "value": "Smith, Jane",
                "kind": "author",
                "identifier": "45678",
                "affiliation": "University",
                "mit_affiliated": True,
            }
        ],
        "dates": [{"range": {"gte": 1901, "lte": 1970}}],
        "notes": [{"value": "Survey Data", "kind": "ResourceType"}],
        "content_type": ["Dataset"],
        "publication_information": ["Harvard Dataverse"],
    }


@pytest.fixture()
def timdex_record_generic_minimal():
    return {
        "timdex_record_id": "123",
        "title": "Dataset 1",
        "identifiers": [{"value": "123"}],
        "source": "Data Provider",
        "source_link": "example://example.example",
    }


@pytest.fixture()
def datacite_record_jpal_full():
    tree = ET.parse(open("tests/fixtures/datacite_record_jpal_full.xml"))
    xml_template = tree.getroot()
    return ET.tostring(
        xml_template,
        encoding="utf8",
        method="xml",
    )


@pytest.fixture()
def datacite_record_jpal_minimal():
    tree = ET.parse(open("tests/fixtures/datacite_record_jpal_minimal.xml"))
    xml_template = tree.getroot()
    return ET.tostring(
        xml_template,
        encoding="utf8",
        method="xml",
    )


@pytest.fixture()
def datacite_records_jpal_full_set():
    tree = ET.parse(open("tests/fixtures/jpal-datacite-full-harvest.xml"))
    xml_template = tree.getroot()
    return ET.tostring(
        xml_template,
        encoding="utf8",
        method="xml",
    )


@pytest.fixture()
def timdex_record_jpal_full():
    return json.load(open("tests/fixtures/timdex_record_jpal_full.json"))


@pytest.fixture()
def timdex_record_jpal_minimal():
    return json.load(open("tests/fixtures/timdex_record_jpal_minimal.json"))
