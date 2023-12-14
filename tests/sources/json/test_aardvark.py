import transmogrifier.models as timdex
from transmogrifier.sources.json.aardvark import Aardvark


def test_aardvark_get_required_fields_returns_expected_values(json_records):
    transformer = Aardvark("cool-repo", json_records)
    assert transformer.get_required_fields(next(json_records)) == {
        "source": "A Cool Repository",
        "source_link": "https://example.com/123",
        "timdex_record_id": "cool-repo:123",
        "title": "Title not provided",
    }


def test_jsontransformer_transform_returns_timdex_record(json_records):
    transformer = Aardvark("cool-repo", json_records)
    assert next(transformer) == timdex.TimdexRecord(
        source="A Cool Repository",
        source_link="https://example.com/123",
        timdex_record_id="cool-repo:123",
        title="Title not provided",
        citation="Title not provided. Geospatial data. https://example.com/123",
        content_type=["Geospatial data"],
    )


def test_aardvark_get_main_titles_success(aardvark_record_all_fields):
    assert Aardvark.get_main_titles(aardvark_record_all_fields) == ["Test title 1"]


def test_aardvark_get_source_record_id_success(aardvark_record_all_fields):
    assert Aardvark.get_source_record_id(aardvark_record_all_fields) == "123"


def test_aardvark_get_subjects_success(aardvark_record_all_fields):
    assert Aardvark.get_subjects(aardvark_record_all_fields) == [
        timdex.Subject(value=["Country"], kind="DCAT Keyword"),
        timdex.Subject(value=["Political boundaries"], kind="DCAT Theme"),
        timdex.Subject(value=["Geography"], kind="Dublin Core Subject"),
        timdex.Subject(value=["Earth"], kind="Dublin Core Subject"),
        timdex.Subject(value=["Dataset"], kind="Subject scheme not provided"),
        timdex.Subject(value=["Vector data"], kind="Subject scheme not provided"),
    ]
