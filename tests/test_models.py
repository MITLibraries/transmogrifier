from pytest import raises

from transmogrifier.models import (
    AlternateTitle,
    Contributor,
    Date,
    Date_Range,
    Identifier,
    Location,
    Note,
    RelatedItem,
    Subject,
)


def test_timdex_record_required_fields_only(timdex_record_required_fields):
    assert timdex_record_required_fields.source == "A Cool Repository"
    assert timdex_record_required_fields.source_link == "https://example.com/"
    assert timdex_record_required_fields.timdex_record_id == "cool-repo:123"
    assert timdex_record_required_fields.title == "Some Data About Trees"
    assert timdex_record_required_fields.alternate_titles is None
    assert timdex_record_required_fields.content_type is None
    assert timdex_record_required_fields.contributors is None
    assert timdex_record_required_fields.dates is None
    assert timdex_record_required_fields.edition is None
    assert timdex_record_required_fields.file_formats is None
    assert timdex_record_required_fields.format is None
    assert timdex_record_required_fields.funding_information is None
    assert timdex_record_required_fields.identifiers is None
    assert timdex_record_required_fields.languages is None
    assert timdex_record_required_fields.locations is None
    assert timdex_record_required_fields.notes is None
    assert timdex_record_required_fields.publication_information is None
    assert timdex_record_required_fields.related_items is None
    assert timdex_record_required_fields.rights is None
    assert timdex_record_required_fields.subjects is None
    assert timdex_record_required_fields.summary is None


def test_timdex_record_required_subfields_only(timdex_record_required_fields):
    timdex_record_required_fields.contributors = [Contributor(value="Smith, Jane")]
    timdex_record_required_fields.identifiers = [Identifier(value="123")]
    timdex_record_required_fields.notes = [Note(value="This book is awesome")]
    timdex_record_required_fields.alternate_titles = [AlternateTitle(value="Alt Title")]
    timdex_record_required_fields.locations = [
        Location(value="Data gathered at a place")
    ]
    timdex_record_required_fields.related_items = [
        RelatedItem(uri="http://doi.example/123")
    ]
    timdex_record_required_fields.subjects = [Subject(value="Stuff")]
    assert timdex_record_required_fields.source == "A Cool Repository"
    assert timdex_record_required_fields.source_link == "https://example.com/"
    assert timdex_record_required_fields.timdex_record_id == "cool-repo:123"
    assert timdex_record_required_fields.title == "Some Data About Trees"
    assert timdex_record_required_fields.alternate_titles[0].value == "Alt Title"
    assert timdex_record_required_fields.content_type is None
    assert timdex_record_required_fields.contributors[0].value == "Smith, Jane"
    assert timdex_record_required_fields.dates is None
    assert timdex_record_required_fields.edition is None
    assert timdex_record_required_fields.file_formats is None
    assert timdex_record_required_fields.format is None
    assert timdex_record_required_fields.funding_information is None
    assert timdex_record_required_fields.identifiers[0].value == "123"
    assert timdex_record_required_fields.languages is None
    assert (
        timdex_record_required_fields.locations[0].value == "Data gathered at a place"
    )
    assert timdex_record_required_fields.notes[0].value == "This book is awesome"
    assert timdex_record_required_fields.publication_information is None
    assert (
        timdex_record_required_fields.related_items[0].uri == "http://doi.example/123"
    )
    assert timdex_record_required_fields.rights is None
    assert timdex_record_required_fields.subjects[0].value == "Stuff"
    assert timdex_record_required_fields.summary is None


def test_timdex_record_all_fields_and_subfields(timdex_record_all_fields_and_subfields):
    assert timdex_record_all_fields_and_subfields.source == "A Cool Repository"
    assert timdex_record_all_fields_and_subfields.source_link == "https://example.com/"
    assert timdex_record_all_fields_and_subfields.timdex_record_id == "cool-repo:123"
    assert timdex_record_all_fields_and_subfields.title == "Some Data About Trees"
    assert (
        timdex_record_all_fields_and_subfields.alternate_titles[0].value == "Alt title"
    )
    assert (
        timdex_record_all_fields_and_subfields.alternate_titles[0].kind == "alternative"
    )
    assert timdex_record_all_fields_and_subfields.content_type == ["dataset"]
    assert timdex_record_all_fields_and_subfields.contributors[0].value == "Smith, Jane"
    assert timdex_record_all_fields_and_subfields.contributors[0].affiliation == ["MIT"]
    assert timdex_record_all_fields_and_subfields.contributors[0].identifier == [
        "https://orcid.org/456"
    ]
    assert timdex_record_all_fields_and_subfields.contributors[0].kind == "author"
    assert timdex_record_all_fields_and_subfields.contributors[0].mit_affiliated is True
    assert timdex_record_all_fields_and_subfields.dates[0].kind == "date of publication"
    assert timdex_record_all_fields_and_subfields.dates[0].value == "2020-01-15"
    assert timdex_record_all_fields_and_subfields.dates[1].kind == "dates collected"
    assert (
        timdex_record_all_fields_and_subfields.dates[1].note
        == "data collected every 3 days"
    )
    assert timdex_record_all_fields_and_subfields.dates[1].range.gt == "2019-01-01"
    assert timdex_record_all_fields_and_subfields.dates[1].range.lt == "2019-06-30"
    assert timdex_record_all_fields_and_subfields.edition == "2nd revision"
    assert timdex_record_all_fields_and_subfields.file_formats == ["application/pdf"]
    assert timdex_record_all_fields_and_subfields.format == "electronic resource"
    assert (
        timdex_record_all_fields_and_subfields.funding_information[0].funder_name
        == "Funding Foundation"
    )
    assert (
        timdex_record_all_fields_and_subfields.funding_information[0].funder_identifier
        == "4356"
    )
    assert (
        timdex_record_all_fields_and_subfields.funding_information[
            0
        ].funder_identifier_type
        == "Crossref FunderID"
    )
    assert (
        timdex_record_all_fields_and_subfields.funding_information[0].award_number
        == "3124"
    )
    assert (
        timdex_record_all_fields_and_subfields.funding_information[0].award_uri
        == "http://awards.example/"
    )
    assert timdex_record_all_fields_and_subfields.identifiers[0].value == "123"
    assert timdex_record_all_fields_and_subfields.identifiers[0].kind == "doi"
    assert timdex_record_all_fields_and_subfields.languages == ["en_US"]
    assert (
        timdex_record_all_fields_and_subfields.locations[0].value
        == "Data gathered at a place"
    )
    assert (
        timdex_record_all_fields_and_subfields.notes[0].value == "This book is awesome"
    )

    assert timdex_record_all_fields_and_subfields.notes[0].kind == "opinion"
    assert timdex_record_all_fields_and_subfields.publication_information == [
        "Version 1.0"
    ]
    assert (
        timdex_record_all_fields_and_subfields.related_items[0].uri
        == "http://doi.example/123"
    )
    assert (
        timdex_record_all_fields_and_subfields.related_items[0].kind == "isReferencedBy"
    )
    assert (
        timdex_record_all_fields_and_subfields.rights[0].description
        == "People may use this"
    )
    assert (
        timdex_record_all_fields_and_subfields.rights[0].uri == "http://rights.example/"
    )
    assert timdex_record_all_fields_and_subfields.subjects[0].value == "Stuff"
    assert timdex_record_all_fields_and_subfields.subjects[0].kind == "LCSH"
    assert timdex_record_all_fields_and_subfields.summary[0] == "This is data."


def test_record_asdict_filters_empty_fields(
    timdex_record_required_fields,
):
    assert timdex_record_required_fields.asdict() == {
        "source": "A Cool Repository",
        "source_link": "https://example.com/",
        "timdex_record_id": "cool-repo:123",
        "title": "Some Data About Trees",
    }


def test_record_asdict_includes_all_fields(timdex_record_all_fields_and_subfields):
    assert timdex_record_all_fields_and_subfields.asdict() == {
        "source": "A Cool Repository",
        "source_link": "https://example.com/",
        "timdex_record_id": "cool-repo:123",
        "title": "Some Data About Trees",
        "alternate_titles": [{"kind": "alternative", "value": "Alt title"}],
        "content_type": ["dataset"],
        "contributors": [
            {
                "value": "Smith, Jane",
                "affiliation": ["MIT"],
                "identifier": ["https://orcid.org/456"],
                "kind": "author",
                "mit_affiliated": True,
            }
        ],
        "dates": [
            {"kind": "date of publication", "value": "2020-01-15"},
            {
                "kind": "dates collected",
                "note": "data collected every 3 days",
                "range": {"gt": "2019-01-01", "lt": "2019-06-30"},
            },
        ],
        "edition": "2nd revision",
        "file_formats": ["application/pdf"],
        "format": "electronic resource",
        "funding_information": [
            {
                "award_number": "3124",
                "award_uri": "http://awards.example/",
                "funder_identifier": "4356",
                "funder_identifier_type": "Crossref FunderID",
                "funder_name": "Funding Foundation",
            }
        ],
        "identifiers": [{"value": "123", "kind": "doi"}],
        "languages": ["en_US"],
        "locations": [{"value": "Data gathered at a place"}],
        "notes": [{"value": "This book is awesome", "kind": "opinion"}],
        "publication_information": ["Version 1.0"],
        "related_items": [{"kind": "isReferencedBy", "uri": "http://doi.example/123"}],
        "rights": [
            {"description": "People may use this", "uri": "http://rights.example/"}
        ],
        "subjects": [{"kind": "LCSH", "value": "Stuff"}],
        "summary": ["This is data."],
    }


def test_timdex_record_date_range_both_gt_and_gte_raises_error(
    timdex_record_required_fields,
):
    with raises(ValueError):
        timdex_record_required_fields.dates = [
            Date(
                range=Date_Range(gt="2019-01-01", gte="2019-01-01", lt="2019-06-30"),
            )
        ]


def test_timdex_record_date_range_both_lt_and_lte_raises_error(
    timdex_record_required_fields,
):
    with raises(ValueError):
        timdex_record_required_fields.dates = [
            Date(
                range=Date_Range(gt="2019-01-01", lt="2019-06-30", lte="2019-06-30"),
            )
        ]


def test_timdex_record_empty_list_raises_error(timdex_record_required_fields):
    with raises(ValueError):
        timdex_record_required_fields.dates = []


def test_timdex_record_list_of_wrong_type_raises_error(timdex_record_required_fields):
    with raises(TypeError):
        timdex_record_required_fields.dates = ["test"]


def test_timdex_record_not_a_list_raises_error(timdex_record_required_fields):
    with raises(TypeError):
        timdex_record_required_fields.dates = "test"
