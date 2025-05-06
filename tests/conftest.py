import pytest
from click.testing import CliRunner

import transmogrifier.models as timdex
from transmogrifier.config import SOURCES, load_external_config
from transmogrifier.sources.jsontransformer import JSONTransformer
from transmogrifier.sources.transformer import Transformer
from transmogrifier.sources.xml.datacite import Datacite
from transmogrifier.sources.xmltransformer import XMLTransformer


@pytest.fixture(autouse=True)
def _test_env(monkeypatch):
    monkeypatch.setenv("WORKSPACE", "test")


@pytest.fixture(autouse=True, scope="session")
def _test_config():
    SOURCES["cool-repo"] = {
        "name": "A Cool Repository",
        "base-url": "https://example.com/",
    }


@pytest.fixture
def _bad_config():
    SOURCES["bad-class-name"] = {
        "name": "Some Repository",
        "base-url": "https://example.com/",
        "transform-class": "transmogrifier.sources.xml.datacite.WrongClass",
    }
    SOURCES["bad-module-path"] = {
        "name": "Some Repository",
        "base-url": "https://example.com/",
        "transform-class": "wrong.module.Datacite",
    }
    yield
    SOURCES.pop("bad-class-name")
    SOURCES.pop("bad-module-path")


@pytest.fixture
def runner():
    return CliRunner()


# transformers ##########################


@pytest.fixture
def generic_transformer():
    class GenericTransformer(Transformer):
        def parse_source_file(self):
            pass

        def record_is_deleted(self):
            pass

        def get_main_titles(self):
            pass

        def get_source_link(self):
            pass

        def get_source_record_id(self):
            pass

        def get_timdex_record_id(self):
            pass

    return GenericTransformer


# aardvark ##########################


@pytest.fixture
def aardvark_records():
    return JSONTransformer.parse_source_file("tests/fixtures/aardvark_records.jsonl")


@pytest.fixture
def aardvark_record_all_fields():
    return JSONTransformer.parse_source_file(
        "tests/fixtures/aardvark/aardvark_record_all_fields.jsonl"
    )


# datacite ##########################


@pytest.fixture
def datacite_records():
    return XMLTransformer.parse_source_file(
        "tests/fixtures/datacite/datacite_records.xml"
    )


@pytest.fixture
def datacite_record_all_fields():
    source_records = XMLTransformer.parse_source_file(
        "tests/fixtures/datacite/datacite_record_all_fields.xml"
    )
    return Datacite("cool-repo", source_records)


# marc ##########################


@pytest.fixture
def loc_country_crosswalk():
    return load_external_config("config/loc-countries.xml", "xml")


@pytest.fixture
def marc_content_type_crosswalk():
    return load_external_config("config/marc_content_type_crosswalk.json", "json")


@pytest.fixture
def oai_pmh_records():
    return XMLTransformer.parse_source_file("tests/fixtures/oai_pmh_records.xml")


# timdex ##########################


@pytest.fixture
def timdex_record_required_fields():
    return timdex.TimdexRecord(
        source="A Cool Repository",
        source_link="https://example.com/123",
        timdex_record_id="cool-repo:123",
        title="Some Data About Trees",
    )


@pytest.fixture
def timdex_record_all_fields_and_subfields():
    return timdex.TimdexRecord(
        citation="Creator (PubYear): Title. Publisher. (resourceTypeGeneral). ID",
        source="A Cool Repository",
        source_link="https://example.com/123",
        timdex_record_id="cool-repo:123",
        title="Some Data About Trees",
        alternate_titles=[timdex.AlternateTitle(value="Alt title", kind="alternative")],
        call_numbers=["QC173.59.S65"],
        content_type=["dataset"],
        contents=["Chapter 1, Chapter 2"],
        contributors=[
            timdex.Contributor(
                value="Smith, Jane",
                affiliation=["MIT"],
                identifier=["https://orcid.org/456"],
                kind="author",
                mit_affiliated=True,
            ),
        ],
        dates=[
            timdex.Date(kind="date of publication", value="2020-01-15"),
            timdex.Date(
                kind="dates collected",
                note="data collected every 3 days",
                range=timdex.DateRange(gt="2019-01-01", lt="2019-06-30"),
            ),
        ],
        edition="2nd revision",
        file_formats=["application/pdf"],
        format="electronic resource",
        funding_information=[
            timdex.Funder(
                funder_name="Funding Foundation",
                funder_identifier="4356",
                funder_identifier_type="Crossref FunderID",
                award_number="3124",
                award_uri="http://awards.example/7689",
            )
        ],
        holdings=[
            timdex.Holding(
                call_number="QC173.59.S65",
                collection="Stacks",
                format="Print volume",
                location="Hayden Library",
                note="Holdings note",
            )
        ],
        identifiers=[timdex.Identifier(value="123", kind="doi")],
        languages=["en_US"],
        links=[
            timdex.Link(
                kind="SpringerLink",
                restrictions="Touchstone authentication required for access",
                text="Direct access via SpringerLink",
                url="http://dx.doi.org/10.1007/978-94-017-0726-8",
            )
        ],
        literary_form="nonfiction",
        locations=[
            timdex.Location(
                value="A point on the globe",
                kind="Data was gathered here",
                geoshape="BBOX(-77.025955, 38.942142)",
            )
        ],
        notes=[timdex.Note(value=["This book is awesome"], kind="opinion")],
        numbering="Began with v. 32, issue 1 (Jan./June 2005).",
        physical_description="1 online resource (1 sound file)",
        publication_frequency=["Semiannual"],
        publishers=[timdex.Publisher(name="Publisher", date="2014", location="A place")],
        related_items=[
            timdex.RelatedItem(
                description="This item is related to this other item",
                item_type="An item type",
                relationship="isReferencedBy",
                uri="http://doi.example/123",
            )
        ],
        rights=[
            timdex.Rights(
                description="People may use this",
                kind="Access rights",
                uri="http://rights.example/",
            ),
        ],
        subjects=[timdex.Subject(value=["Stuff"], kind="LCSH")],
        summary=["This is data."],
    )


# timdex parquet dataset ##########################


@pytest.fixture
def run_id():
    return "run-abc-123"


@pytest.fixture
def empty_dataset_location(tmp_path):
    return str(tmp_path / "dataset")


@pytest.fixture
def libguides_input_file():
    return (
        "tests/fixtures/dataset/libguides-2024-06-03-full-extracted-records-to-index.xml"
    )


@pytest.fixture
def empty_libguides_input_file():
    return (
        "tests/fixtures/dataset/libguides-2024-06-04-full-extracted-records-to-index.xml"
    )


@pytest.fixture
def libguides_transformer(monkeypatch, run_id, libguides_input_file):
    monkeypatch.setenv("ETL_VERSION", "2")
    return Transformer.load(
        "libguides",
        libguides_input_file,
        run_id=run_id,
    )
