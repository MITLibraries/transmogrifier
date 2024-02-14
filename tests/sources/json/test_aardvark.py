from pathlib import Path

import pytest

import transmogrifier.models as timdex
from transmogrifier.sources.json.aardvark import MITAardvark


def test_mitaardvark_transform_and_write_output_files_writes_output_files(
    tmp_path, aardvark_records
):
    output_file = str(tmp_path / "output_file.json")
    transformer = MITAardvark("cool-repo", aardvark_records)
    assert not Path(tmp_path / "output_file.json").exists()
    assert not Path(tmp_path / "output_file.txt").exists()
    transformer.transform_and_write_output_files(output_file)
    assert Path(tmp_path / "output_file.json").exists()
    assert Path(tmp_path / "output_file.txt").exists()


def test_mitaardvark_transform_and_write_output_files_no_txt_file_if_not_needed(
    tmp_path, aardvark_record_all_fields
):
    output_file = str(tmp_path / "output_file.json")
    transformer = MITAardvark("cool-repo", aardvark_record_all_fields)
    transformer.transform_and_write_output_files(output_file)
    assert len(list(tmp_path.iterdir())) == 1
    assert next(tmp_path.iterdir()).name == "output_file.json"


def test_aardvark_get_required_fields_returns_expected_values(aardvark_records):
    transformer = MITAardvark("cool-repo", aardvark_records)
    assert transformer.get_required_fields(next(aardvark_records)) == {
        "source": "A Cool Repository",
        "source_link": "https://example.com/gismit:123",
        "timdex_record_id": "cool-repo:123",
        "title": "Test title 1",
    }


def test_aardvark_transform_returns_timdex_record(aardvark_records):
    transformer = MITAardvark("cool-repo", aardvark_records)
    assert next(transformer) == timdex.TimdexRecord(
        source="A Cool Repository",
        source_link="https://example.com/gismit:123",
        timdex_record_id="cool-repo:123",
        title="Test title 1",
        citation="Test title 1. Geospatial data. https://example.com/gismit:123",
        content_type=["Geospatial data"],
        rights=[timdex.Rights(description="Access rights", kind="Access")],
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


def test_aardvark_record_is_deleted_returns_false_if_field_missing(
    aardvark_record_all_fields,
):
    assert MITAardvark.record_is_deleted(next(aardvark_record_all_fields)) is False


def test_aardvark_record_is_deleted_raises_error_if_value_is_string(
    aardvark_record_all_fields,
):
    aardvark_record = next(aardvark_record_all_fields)
    aardvark_record["gbl_suppressed_b"] = "True"
    with pytest.raises(
        ValueError,
        match="Record ID '123': 'gbl_suppressed_b' value is not a boolean",
    ):
        MITAardvark.record_is_deleted(aardvark_record)


def test_aardvark_record_is_deleted_returns_false_if_value_is_false(
    aardvark_record_all_fields,
):
    aardvark_record = next(aardvark_record_all_fields)
    aardvark_record["gbl_suppressed_b"] = False
    assert MITAardvark.record_is_deleted(aardvark_record) is False


def test_aardvark_record_is_deleted_success(aardvark_record_all_fields):
    aardvark_record = next(aardvark_record_all_fields)
    aardvark_record["gbl_suppressed_b"] = True
    assert MITAardvark.record_is_deleted(aardvark_record) is True


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


def test_aardvark_get_dates_success(aardvark_record_all_fields):
    assert MITAardvark.get_dates(next(aardvark_record_all_fields), "123") == [
        timdex.Date(kind="Issued", value="2003-10-23"),
        timdex.Date(kind="Coverage", value="1943"),
        timdex.Date(kind="Coverage", value="1979"),
        timdex.Date(kind="Coverage", value="1944"),
        timdex.Date(kind="Coverage", value="1945"),
        timdex.Date(kind="Coverage", value="1946"),
        timdex.Date(
            kind="Coverage",
            range=timdex.DateRange(gte="1943", lte="1946"),
        ),
    ]


def test_aardvark_get_dates_drops_dates_with_invalid_strings(aardvark_record_all_fields):
    record = next(aardvark_record_all_fields)
    record["dct_issued_s"] = "1933?"  # dropped
    record["dct_temporal_sm"] = [
        "2000-01-01",
        "1999",
        "approximately 1569",  # dropped
        "absolute junky date",  # dropped
    ]
    record["gbl_dateRange_drsim"] = ["[1943 TO 1946]"]
    assert MITAardvark.get_dates(record, "123") == [
        timdex.Date(kind="Coverage", note=None, range=None, value="2000-01-01"),
        timdex.Date(kind="Coverage", note=None, range=None, value="1999"),
        timdex.Date(kind="Coverage", note=None, range=None, value="1943"),
        timdex.Date(kind="Coverage", note=None, range=None, value="1944"),
        timdex.Date(kind="Coverage", note=None, range=None, value="1945"),
        timdex.Date(kind="Coverage", note=None, range=None, value="1946"),
        timdex.Date(
            kind="Coverage",
            note=None,
            range=timdex.DateRange(gt=None, gte="1943", lt=None, lte="1946"),
            value=None,
        ),
    ]


def test_aardvark_parse_solr_date_range_string_success():
    assert MITAardvark.parse_solr_date_range_string("[1932 TO 1937]", "123") == (
        "1932",
        "1937",
    )


def test_parse_solr_date_range_invalid_date_range_string_raises_error():
    with pytest.raises(
        ValueError,
        match="Record ID '123': Unable to parse date range string 'Invalid'",
    ):
        MITAardvark.parse_solr_date_range_string("Invalid", "123")


def test_aardvark_get_identifiers_success(aardvark_record_all_fields):
    assert MITAardvark.get_identifiers(next(aardvark_record_all_fields)) == [
        timdex.Identifier(value="abc123", kind="Not specified")
    ]


def test_aardvark_get_links_success(aardvark_record_all_fields):
    assert MITAardvark.get_links(next(aardvark_record_all_fields), "123") == [
        timdex.Link(
            url="https://cdn.dev1.mitlibrary.net/geo/public"
            "/GISPORTAL_GISOWNER01_BOSTONWATER95.source.fgdc.xml",
            kind="Download",
            text="Source Metadata",
        ),
        timdex.Link(
            url="https://cdn.dev1.mitlibrary.net/geo/public"
            "/GISPORTAL_GISOWNER01_BOSTONWATER95."
            "normalized.aardvark.json",
            kind="Download",
            text="Aardvark Metadata",
        ),
        timdex.Link(
            url="https://cdn.dev1.mitlibrary.net/geo/public"
            "/GISPORTAL_GISOWNER01_BOSTONWATER95.zip",
            kind="Download",
            text="Data",
        ),
        timdex.Link(
            url="https://geodata.libraries.mit.edu/record/gismit"
            ":GISPORTAL_GISOWNER01_BOSTONWATER95",
            kind="Website",
            text="Website",
        ),
    ]


def test_aardvark_get_links_logs_warning_for_invalid_json(caplog):
    assert MITAardvark.get_links({"dct_references_s": "Invalid"}, "123") == []
    assert (
        "Record ID '123': Unable to parse links string 'Invalid' as JSON" in caplog.text
    )


def test_aardvark_get_locations_success(aardvark_record_all_fields):
    assert MITAardvark.get_locations(next(aardvark_record_all_fields), "123") == [
        timdex.Location(
            kind="Bounding Box", geoshape="BBOX (-111.1, -104.0, 45.0, 40.9)"
        ),
        timdex.Location(kind="Geometry", geoshape="BBOX (-111.1, -104.0, 45.0, 40.9)"),
    ]


def test_parse_get_locations_string_invalid_geostring_logs_warning(
    aardvark_record_all_fields, caplog
):
    aardvark_record = next(aardvark_record_all_fields)
    aardvark_record["dcat_bbox"] = "Invalid"
    aardvark_record["locn_geometry"] = "Invalid"
    assert MITAardvark.get_locations(aardvark_record, "123") == []
    assert (
        "Record ID '123': Unable to parse geodata string 'Invalid' in 'dcat_bbox'"
        in caplog.text
    )
    assert (
        "Record ID '123': Unable to parse geodata string 'Invalid' in 'locn_geometry'"
        in caplog.text
    )


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
    assert MITAardvark.get_publication_information(next(aardvark_record_all_fields)) == [
        "ML InfoMap (Firm)",
        "MIT",
    ]


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
        timdex.Subject(value=["Country"], kind="DCAT; Keyword"),
        timdex.Subject(value=["Political boundaries"], kind="DCAT; Theme"),
        timdex.Subject(value=["Some city, Some country"], kind="Dublin Core; Spatial"),
        timdex.Subject(value=["Geography"], kind="Dublin Core; Subject"),
        timdex.Subject(value=["Earth"], kind="Dublin Core; Subject"),
        timdex.Subject(value=["Dataset"], kind="Subject scheme not provided"),
        timdex.Subject(value=["Vector data"], kind="Subject scheme not provided"),
    ]
