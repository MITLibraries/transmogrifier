import transmogrifier.models as timdex
from transmogrifier.sources.json.aardvark import MITAardvark


def test_aardvark_get_required_fields_returns_expected_values(aardvark_records):
    transformer = MITAardvark("cool-repo", aardvark_records)
    assert transformer.get_required_fields(next(aardvark_records)) == {
        "source": "A Cool Repository",
        "source_link": "https://example.com/123",
        "timdex_record_id": "cool-repo:123",
        "title": "Test title 1",
    }


def test_aardvark_transform_returns_timdex_record(aardvark_records):
    transformer = MITAardvark("cool-repo", aardvark_records)
    assert next(transformer) == timdex.TimdexRecord(
        source="A Cool Repository",
        source_link="https://example.com/123",
        timdex_record_id="cool-repo:123",
        title="Test title 1",
        citation="Test title 1. Geospatial data. https://example.com/123",
        content_type=["Geospatial data"],
    )


def test_aardvark_get_optional_fields_non_field_method_values_success(
    aardvark_record_all_fields,
):
    transformer = MITAardvark("cool-repo", aardvark_record_all_fields)
    record = next(transformer)
    assert record.format == "Shapefile"
    assert record.languages == ["eng"]
    assert record.summary == ["A description"]


def test_aardvark_get_main_titles_success(aardvark_record_all_fields):
    assert MITAardvark.get_main_titles(next(aardvark_record_all_fields)) == [
        "Test title 1"
    ]


def test_aardvark_get_source_record_id_success(aardvark_record_all_fields):
    assert MITAardvark.get_source_record_id(next(aardvark_record_all_fields)) == "123"


def test_aardvark_get_alternate_titles_success(aardvark_record_all_fields):
    assert MITAardvark.get_alternate_titles(next(aardvark_record_all_fields)) == [
        timdex.AlternateTitle(value="Alternate title")
    ]


def test_aardvark_get_contributors_success(aardvark_record_all_fields):
    assert MITAardvark.get_contributors(next(aardvark_record_all_fields)) == [
        timdex.Contributor(
            value="Smith, Jane",
            kind="Creator",
        ),
        timdex.Contributor(
            value="Smith, John",
            kind="Creator",
        ),
    ]


def test_aardvark_get_notes_success(aardvark_record_all_fields):
    assert MITAardvark.get_notes(next(aardvark_record_all_fields)) == [
        timdex.Note(
            value=["Danger: This text will be displayed in a red box"],
            kind="Display note",
        ),
        timdex.Note(
            value=["Info: This text will be displayed in a blue box"],
            kind="Display note",
        ),
        timdex.Note(
            value=["Tip: This text will be displayed in a green box"],
            kind="Display note",
        ),
        timdex.Note(
            value=["Warning: This text will be displayed in a yellow box"],
            kind="Display note",
        ),
        timdex.Note(
            value=[
                "This is text without a tag and it will be assigned default 'note' style"
            ],
            kind="Display note",
        ),
    ]


def test_aardvark_get_publication_information_success(aardvark_record_all_fields):
    assert MITAardvark.get_publication_information(
        next(aardvark_record_all_fields)
    ) == ["ML InfoMap (Firm)", "MIT"]


def test_aardvark_get_rights_success(aardvark_record_all_fields):
    assert MITAardvark.get_rights(next(aardvark_record_all_fields)) == [
        timdex.Rights(description="Access note", kind="Access"),
        timdex.Rights(uri="http://license.license"),
        timdex.Rights(uri="http://another_license.another_license"),
        timdex.Rights(description="Some person has the rights"),
        timdex.Rights(
            description="The person with the rights. Another person with the rights"
        ),
    ]


def test_aardvark_get_subjects_success(aardvark_record_all_fields):
    assert MITAardvark.get_subjects(next(aardvark_record_all_fields)) == [
        timdex.Subject(value=["Country"], kind="DCAT Keyword"),
        timdex.Subject(value=["Political boundaries"], kind="DCAT Theme"),
        timdex.Subject(value=["Geography"], kind="Dublin Core Subject"),
        timdex.Subject(value=["Earth"], kind="Dublin Core Subject"),
        timdex.Subject(value=["Dataset"], kind="Subject scheme not provided"),
        timdex.Subject(value=["Vector data"], kind="Subject scheme not provided"),
    ]
