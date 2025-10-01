import json

import pytest

import transmogrifier.models as timdex
from transmogrifier.sources.json.aardvark import MITAardvark


def create_aardvark_source_record_stub() -> dict:
    return {"id": "123", "dct_title_s": "Test title 1"}


def test_aardvark_transform_returns_timdex_record(aardvark_records):
    aardvark = MITAardvark("cool-repo", aardvark_records)
    timdex_record = aardvark.transform(next(aardvark.source_records))
    assert timdex_record == timdex.TimdexRecord(
        source="A Cool Repository",
        source_link="https://geodata.libraries.mit.edu/record/abc:123",
        timdex_record_id="cool-repo:123",
        title="Test title 1",
        citation="Test title 1. https://geodata.libraries.mit.edu/record/abc:123",
        content_type=["Not specified"],
        rights=[timdex.Rights(description="Access rights", kind="Access rights")],
        links=[
            timdex.Link(
                url="https://geodata.libraries.mit.edu/record/abc:123",
                kind="Website",
                restrictions=None,
                text="Website",
            )
        ],
    )


def test_aardvark_get_main_titles_success():
    source_record = create_aardvark_source_record_stub()
    assert MITAardvark.get_main_titles(source_record) == ["Test title 1"]


def test_aardvark_record_get_source_link_success():
    source_record = create_aardvark_source_record_stub()
    url_from_source_record = "https://geodata.libraries.mit.edu/record/abc:123"
    source_record["gbl_suppressed_b"] = False
    source_record["dct_references_s"] = json.dumps(
        {"http://schema.org/url": url_from_source_record}
    )
    aardvark = MITAardvark("cool-repo", iter([source_record]))
    assert aardvark.get_source_link(source_record) == url_from_source_record


def test_aardvark_record_get_source_link_bad_dct_references_s_raises_error():
    source_record = create_aardvark_source_record_stub()
    source_record["dct_references_s"] = json.dumps(
        {"missing data": "from aardvark from geoharvester"}
    )
    aardvark = MITAardvark("cool-repo", iter([source_record]))
    with pytest.raises(
        ValueError,
        match=r"Could not locate a kind=Website link to pull the source link from.",
    ):
        aardvark.get_source_link(source_record)


def test_aardvark_record_get_timdex_record_id_success():
    source_record = create_aardvark_source_record_stub()
    aardvark = MITAardvark("cool-repo", iter([source_record]))
    assert aardvark.get_timdex_record_id(source_record) == "cool-repo:123"


def test_aardvark_get_source_record_id_success():
    source_record = create_aardvark_source_record_stub()
    assert MITAardvark.get_source_record_id(source_record) == "123"


def test_aardvark_record_is_deleted_success():
    source_record = create_aardvark_source_record_stub()
    source_record["gbl_suppressed_b"] = True
    assert MITAardvark.record_is_deleted(source_record) is True


def test_aardvark_record_is_deleted_raises_error_if_field_missing():
    source_record = create_aardvark_source_record_stub()
    with pytest.raises(
        ValueError,
        match="Record ID '123': 'gbl_suppressed_b' value is not a boolean or missing",
    ):
        MITAardvark.record_is_deleted(source_record)


def test_aardvark_record_is_deleted_raises_error_if_value_is_string():
    source_record = create_aardvark_source_record_stub()
    source_record["gbl_suppressed_b"] = "True"
    with pytest.raises(
        ValueError,
        match="Record ID '123': 'gbl_suppressed_b' value is not a boolean or missing",
    ):
        MITAardvark.record_is_deleted(source_record)


def test_aardvark_record_is_deleted_returns_false_if_value_is_false():
    source_record = create_aardvark_source_record_stub()
    source_record["gbl_suppressed_b"] = False
    assert MITAardvark.record_is_deleted(source_record) is False


def test_aardvark_get_alternate_titles_success():
    source_record = create_aardvark_source_record_stub()
    source_record["dct_alternative_sm"] = ["Alternate title"]
    assert MITAardvark.get_alternate_titles(source_record) == [
        timdex.AlternateTitle(value="Alternate title")
    ]


def test_aardvark_get_alternate_titles_transforms_correctly_if_fields_blank():
    source_record = create_aardvark_source_record_stub()
    source_record["dct_alternative_sm"] = []
    assert MITAardvark.get_alternate_titles(source_record) is None


def test_aardvark_get_alternate_titles_transforms_correctly_if_fields_missing():
    source_record = {}
    assert MITAardvark.get_alternate_titles(source_record) is None


def test_aardvark_get_content_type_success():
    source_record = create_aardvark_source_record_stub()
    source_record["gbl_resourceType_sm"] = ["Vector data"]
    assert MITAardvark.get_content_type(source_record) == ["Vector data"]


def test_aardvark_get_content_type_transforms_correctly_if_fields_blank():
    source_record = create_aardvark_source_record_stub()
    source_record["gbl_resourceType_sm"] = []
    assert MITAardvark.get_content_type(source_record) is None


def test_aardvark_get_content_type_transforms_correctly_if_fields_missing():
    source_record = {}
    assert MITAardvark.get_content_type(source_record) is None


def test_aardvark_get_contributors_success():
    source_record = create_aardvark_source_record_stub()
    source_record["dct_creator_sm"] = ["Smith, Jane", "Smith, John"]
    assert MITAardvark.get_contributors(source_record) == [
        timdex.Contributor(
            value="Smith, Jane",
            kind="Creator",
        ),
        timdex.Contributor(
            value="Smith, John",
            kind="Creator",
        ),
    ]


def test_aardvark_get_contributors_transforms_correctly_if_fields_blank():
    source_record = create_aardvark_source_record_stub()
    source_record["dct_creator_sm"] = []
    assert MITAardvark.get_contributors(source_record) is None


def test_aardvark_get_contributors_transforms_correctly_if_fields_missing():
    source_record = {}
    assert MITAardvark.get_contributors(source_record) is None


def test_aardvark_get_dates_success():
    source_record = create_aardvark_source_record_stub()
    source_record["dct_issued_s"] = "2003-10-23"
    source_record["dct_temporal_sm"] = ["1943", "1979"]
    source_record["gbl_dateRange_drsim"] = ["[1943 TO 1946]"]
    source_record["gbl_indexYear_im"] = [1943, 1944, 1945, 1946]
    assert MITAardvark.get_dates(source_record) == [
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


def test_aardvark_get_dates_transforms_correctly_if_fields_blank():
    source_record = create_aardvark_source_record_stub()
    source_record["dct_issued_s"] = ""
    source_record["dct_temporal_sm"] = []
    source_record["gbl_dateRange_drsim"] = []
    source_record["gbl_indexYear_im"] = []
    assert MITAardvark.get_dates(source_record) is None


def test_aardvark_get_dates_transforms_correctly_if_fields_missing():
    source_record = {}
    assert MITAardvark.get_dates(source_record) is None


def test_aardvark_get_dates_drops_dates_with_invalid_strings(caplog):
    caplog.set_level("DEBUG")
    source_record = create_aardvark_source_record_stub()
    source_record["dct_issued_s"] = "1933?"  # dropped
    source_record["dct_temporal_sm"] = [
        "2000-01-01",
        "1999",
        "approximately 1569",  # dropped
        "absolute junky date",  # dropped
    ]
    source_record["gbl_dateRange_drsim"] = [
        "[1943 TO 1946]",
        "[apples TO oranges]",  # logged and dropped
    ]
    source_record["gbl_indexYear_im"] = [1943, 1944, 1945, 1946]
    assert MITAardvark.get_dates(source_record) == [
        timdex.Date(kind="Coverage", value="2000-01-01"),
        timdex.Date(kind="Coverage", value="1999"),
        timdex.Date(kind="Coverage", value="1943"),
        timdex.Date(kind="Coverage", value="1944"),
        timdex.Date(kind="Coverage", value="1945"),
        timdex.Date(kind="Coverage", value="1946"),
        timdex.Date(
            kind="Coverage",
            range=timdex.DateRange(gte="1943", lte="1946"),
        ),
    ]
    assert "Unable to parse date range string" in caplog.text


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


def test_aardvark_get_format_type_success():
    source_record = create_aardvark_source_record_stub()
    source_record["dct_format_s"] = ["Shapefile"]
    assert MITAardvark.get_format(source_record) == ["Shapefile"]


def test_aardvark_get_format_transforms_correctly_if_fields_blank():
    source_record = create_aardvark_source_record_stub()
    source_record["dct_format_s"] = []
    assert MITAardvark.get_format(source_record) is None


def test_aardvark_get_format_transforms_correctly_if_fields_missing():
    source_record = {}
    assert MITAardvark.get_format(source_record) is None


def test_aardvark_get_identifiers_success():
    source_record = create_aardvark_source_record_stub()
    source_record["dct_identifier_sm"] = ["abc123"]
    assert MITAardvark.get_identifiers(source_record) == [
        timdex.Identifier(value="abc123", kind="Not specified")
    ]


def test_aardvark_get_identifiers_transforms_correctly_if_fields_blank():
    source_record = create_aardvark_source_record_stub()
    source_record["dct_identifier_sm"] = []
    assert MITAardvark.get_identifiers(source_record) is None


def test_aardvark_get_identifiers_transforms_correctly_if_fields_missing():
    source_record = {}
    assert MITAardvark.get_identifiers(source_record) is None


def test_aardvark_get_languages_success():
    source_record = create_aardvark_source_record_stub()
    source_record["dct_language_sm"] = ["eng"]
    assert MITAardvark.get_languages(source_record) == ["eng"]


def test_aardvark_get_languages_transforms_correctly_if_fields_blank():
    source_record = create_aardvark_source_record_stub()
    source_record["dct_language_sm"] = []
    assert MITAardvark.get_languages(source_record) is None


def test_aardvark_get_languages_transforms_correctly_if_fields_missing():
    source_record = {}
    assert MITAardvark.get_languages(source_record) is None


def test_aardvark_get_links_success():
    source_record = create_aardvark_source_record_stub()
    source_record["dct_references_s"] = (
        '{"http://schema.org/downloadUrl": [{"label": "Source Metadata", "url": '
        '"https://cdn.dev1.mitlibrary.net/geo/public/GISPORTAL_GISOWNER01_BOSTONWATER95'
        '.source.fgdc.xml"}, {"label": "Aardvark Metadata", "url": '
        '"https://cdn.dev1.mitlibrary.net/geo/public/GISPORTAL_GISOWNER01_BOSTONWATER95'
        '.normalized.aardvark.json"}, {"label": "Data", "url": '
        '"https://cdn.dev1.mitlibrary.net/geo/public/GISPORTAL_GISOWNER01_BOSTONWATER95'
        '.zip"}], "http://schema.org/url": "https://geodata.libraries.mit.edu/record/'
        'gismit:GISPORTAL_GISOWNER01_BOSTONWATER95"}'
    )
    assert MITAardvark.get_links(source_record) == [
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


def test_aardvark_get_links_transforms_correctly_if_fields_blank():
    source_record = create_aardvark_source_record_stub()
    source_record["dct_references_s"] = ""
    assert MITAardvark.get_links(source_record) is None


def test_aardvark_get_links_transforms_correctly_if_fields_missing():
    source_record = create_aardvark_source_record_stub()
    assert MITAardvark.get_links(source_record) is None


def test_aardvark_get_links_logs_warning_for_invalid_json(caplog):
    source_record = create_aardvark_source_record_stub()
    source_record["dct_references_s"] = "Invalid"
    assert MITAardvark.get_links(source_record) is None
    assert (
        "Record ID '123': Unable to parse links string 'Invalid' as JSON" in caplog.text
    )


def test_aardvark_get_locations_success():
    source_record = create_aardvark_source_record_stub()
    source_record["dcat_bbox"] = "ENVELOPE(-111.1, -104.0, 45.0, 40.9)"
    source_record["locn_geometry"] = "ENVELOPE(-111.1, -104.0, 45.0, 40.9)"
    assert MITAardvark.get_locations(source_record) == [
        timdex.Location(
            kind="Bounding Box", geoshape="BBOX (-111.1, -104.0, 45.0, 40.9)"
        ),
        timdex.Location(kind="Geometry", geoshape="BBOX (-111.1, -104.0, 45.0, 40.9)"),
    ]


def test_aardvark_get_locations_transforms_correctly_if_fields_blank():
    source_record = create_aardvark_source_record_stub()
    source_record["dcat_bbox"] = ""
    source_record["locn_geometry"] = ""
    assert MITAardvark.get_locations(source_record) is None


def test_aardvark_get_locations_transforms_correctly_if_fields_missing():
    source_record = create_aardvark_source_record_stub()
    assert MITAardvark.get_locations(source_record) is None


def test_parse_get_locations_string_invalid_geostring_logs_warning(caplog):
    source_record = create_aardvark_source_record_stub()
    source_record["dcat_bbox"] = "Invalid"
    source_record["locn_geometry"] = "Invalid"
    assert MITAardvark.get_locations(source_record) is None
    assert (
        "Record ID '123': Unable to parse geodata string 'Invalid' in 'dcat_bbox'"
        in caplog.text
    )
    assert (
        "Record ID '123': Unable to parse geodata string 'Invalid' in 'locn_geometry'"
        in caplog.text
    )


def test_aardvark_get_notes_success():
    source_record = create_aardvark_source_record_stub()
    source_record["gbl_displayNote_sm"] = [
        "Danger: This text will be displayed in a red box",
        "Info: This text will be displayed in a blue box",
        "Tip: This text will be displayed in a green box",
        "Warning: This text will be displayed in a yellow box",
        "This is text without a tag and it will be assigned default 'note' style",
    ]
    assert MITAardvark.get_notes(source_record) == [
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


def test_aardvark_get_notes_transforms_correctly_if_fields_blank():
    source_record = create_aardvark_source_record_stub()
    source_record["gbl_displayNote_sm"] = []
    assert MITAardvark.get_notes(source_record) is None


def test_aardvark_get_notes_transforms_correctly_if_fields_missing():
    source_record = create_aardvark_source_record_stub()
    assert MITAardvark.get_notes(source_record) is None


def test_aardvark_get_provider_success():
    source_record = create_aardvark_source_record_stub()
    source_record["schema_provider_s"] = "MIT"
    assert MITAardvark.get_provider(source_record) == "MIT"


def test_aardvark_get_provider_transforms_correctly_if_fields_blank():
    source_record = create_aardvark_source_record_stub()
    source_record["schema_provider_s"] = ""
    assert MITAardvark.get_provider(source_record) is None


def test_aardvark_get_provider_transforms_correctly_if_fields_missing():
    source_record = create_aardvark_source_record_stub()
    assert MITAardvark.get_provider(source_record) is None


def test_aardvark_get_publishers_success():
    source_record = create_aardvark_source_record_stub()
    source_record["dct_publisher_sm"] = ["ML InfoMap (Firm)"]
    assert MITAardvark.get_publishers(source_record) == [
        timdex.Publisher(name="ML InfoMap (Firm)")
    ]


def test_aardvark_get_publishers_transforms_correctly_if_fields_blank():
    source_record = create_aardvark_source_record_stub()
    source_record["dct_publisher_sm"] = []
    assert MITAardvark.get_publishers(source_record) is None


def test_aardvark_get_publishers_transforms_correctly_if_fields_missing():
    source_record = create_aardvark_source_record_stub()
    assert MITAardvark.get_publishers(source_record) is None


def test_aardvark_get_rights_success():
    source_record = create_aardvark_source_record_stub()
    source_record["dct_accessRights_s"] = "Access note"
    source_record["dct_license_sm"] = [
        "http://license.license",
        "http://another_license.another_license",
    ]
    source_record["dct_rights_sm"] = ["Some person has the rights"]
    source_record["dct_rightsHolder_sm"] = [
        "The person with the rights",
        "Another person with the rights",
    ]
    aardvark = MITAardvark("cool-repo", iter([source_record]))
    assert aardvark.get_rights(source_record) == [
        timdex.Rights(description="Access note", kind="Access rights"),
        timdex.Rights(uri="http://license.license"),
        timdex.Rights(uri="http://another_license.another_license"),
        timdex.Rights(description="Some person has the rights"),
        timdex.Rights(
            description="The person with the rights. Another person with the rights"
        ),
    ]


def test_aardvark_get_rights_mit_restricted_success():
    source_record = create_aardvark_source_record_stub()
    source_record["dct_accessRights_s"] = "Restricted"
    aardvark = MITAardvark("gismit", iter([source_record]))
    assert aardvark.get_rights(source_record) == [
        timdex.Rights(description="Restricted", kind="Access rights"),
        timdex.Rights(description="MIT authentication required", kind="Access to files"),
    ]


def test_aardvark_get_rights_mit_public_success():
    source_record = create_aardvark_source_record_stub()
    source_record["dct_accessRights_s"] = "Public"
    aardvark = MITAardvark("gismit", iter([source_record]))
    assert aardvark.get_rights(source_record) == [
        timdex.Rights(description="Public", kind="Access rights"),
        timdex.Rights(description="no authentication required", kind="Access to files"),
    ]


def test_aardvark_get_rights_external_restricted_success():
    source_record = create_aardvark_source_record_stub()
    source_record["dct_accessRights_s"] = "Restricted"
    aardvark = MITAardvark("gisogm", iter([source_record]))
    assert aardvark.get_rights(source_record) == [
        timdex.Rights(description="Restricted", kind="Access rights"),
        timdex.Rights(
            description="unknown: check with owning institution", kind="Access to files"
        ),
    ]


def test_aardvark_get_rights_external_public_success():
    source_record = create_aardvark_source_record_stub()
    source_record["dct_accessRights_s"] = "Public"
    aardvark = MITAardvark("gisogm", iter([source_record]))
    assert aardvark.get_rights(source_record) == [
        timdex.Rights(description="Public", kind="Access rights"),
        timdex.Rights(
            description="unknown: check with owning institution", kind="Access to files"
        ),
    ]


def test_aardvark_get_subjects_success():
    source_record = create_aardvark_source_record_stub()
    source_record["dcat_keyword_sm"] = ["Country"]
    source_record["dcat_theme_sm"] = ["Political boundaries"]
    source_record["dct_spatial_sm"] = ["Some city, Some country"]
    source_record["dct_subject_sm"] = ["Geography", "Earth"]
    source_record["gbl_resourceClass_sm"] = ["Dataset"]
    assert MITAardvark.get_subjects(source_record) == [
        timdex.Subject(value=["Country"], kind="DCAT; Keyword"),
        timdex.Subject(value=["Political boundaries"], kind="DCAT; Theme"),
        timdex.Subject(value=["Some city, Some country"], kind="Dublin Core; Spatial"),
        timdex.Subject(value=["Geography"], kind="Dublin Core; Subject"),
        timdex.Subject(value=["Earth"], kind="Dublin Core; Subject"),
        timdex.Subject(value=["Dataset"], kind="Subject scheme not provided"),
    ]


def test_aardvark_get_subjects_transforms_correctly_if_fields_blank():
    source_record = create_aardvark_source_record_stub()
    source_record["dcat_keyword_sm"] = []
    source_record["dcat_theme_sm"] = []
    source_record["dct_spatial_sm"] = []
    source_record["dct_subject_sm"] = []
    source_record["gbl_resourceClass_sm"] = []
    assert MITAardvark.get_subjects(source_record) is None


def test_aardvark_get_subjects_transforms_correctly_if_fields_missing():
    source_record = create_aardvark_source_record_stub()
    assert MITAardvark.get_subjects(source_record) is None


def test_aardvark_get_summary_success():
    source_record = create_aardvark_source_record_stub()
    source_record["dct_description_sm"] = ["A description"]
    assert MITAardvark.get_summary(source_record) == ["A description"]


def test_aardvark_get_summary_transforms_correctly_if_fields_blank():
    source_record = create_aardvark_source_record_stub()
    source_record["dct_description_sm"] = []
    assert MITAardvark.get_summary(source_record) is None


def test_aardvark_get_summary_transforms_correctly_if_fields_missing():
    source_record = create_aardvark_source_record_stub()
    assert MITAardvark.get_summary(source_record) is None
