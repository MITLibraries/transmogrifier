from pytest import raises

from transmogrifier.models import (
    Contributor,
    Date,
    Date_Range,
    Identifier,
    Note,
    TimdexRecord,
)


def test_timdex_record_required_fields_only(timdex_record):
    assert timdex_record.source == "A Cool Repository"
    assert timdex_record.source_link == "https://example.com/item123"
    assert timdex_record.timdex_record_id == "cool-repo:123"
    assert timdex_record.title == "Some Data About Trees"
    assert timdex_record.content_type is None
    assert timdex_record.contributors is None
    assert timdex_record.dates is None
    assert timdex_record.identifiers is None
    assert timdex_record.notes is None
    assert timdex_record.publication_information is None


def test_timdex_record_required_subfields_only(timdex_record):
    timdex_record.contributors = [Contributor(value="Smith, Jane")]
    timdex_record.identifiers = [Identifier(value="123")]
    timdex_record.notes = [Note(value=["This book is awesome"])]
    assert timdex_record.source == "A Cool Repository"
    assert timdex_record.source_link == "https://example.com/item123"
    assert timdex_record.timdex_record_id == "cool-repo:123"
    assert timdex_record.title == "Some Data About Trees"
    assert timdex_record.content_type is None
    assert timdex_record.contributors[0].value == "Smith, Jane"
    assert timdex_record.dates is None
    assert timdex_record.identifiers[0].value == "123"
    assert timdex_record.notes[0].value == ["This book is awesome"]
    assert timdex_record.publication_information is None


def test_timdex_record_all_fields_and_subfields(timdex_record):
    timdex_record.content_type = ["dataset"]
    timdex_record.contributors = [
        Contributor(
            value="Smith, Jane",
            affiliation=["MIT"],
            identifier=["https://orcid.org/456"],
            kind="author",
            mit_affiliated=True,
        ),
    ]
    timdex_record.dates = [
        Date(kind="date of publication", value="2020-01-15"),
        Date(
            kind="dates collected",
            note="data collected every 3 days",
            range=Date_Range(gt="2019-01-01", lt="2019-06-30"),
        ),
    ]
    timdex_record.identifiers = [Identifier(value="123", kind="doi")]
    timdex_record.notes = [Note(value=["This book is awesome"], kind="opinion")]
    timdex_record.publication_information = ["Version 1.0"]
    assert timdex_record.source == "A Cool Repository"
    assert timdex_record.source_link == "https://example.com/item123"
    assert timdex_record.timdex_record_id == "cool-repo:123"
    assert timdex_record.title == "Some Data About Trees"
    assert timdex_record.content_type == ["dataset"]
    assert timdex_record.contributors[0].value == "Smith, Jane"
    assert timdex_record.contributors[0].affiliation == ["MIT"]
    assert timdex_record.contributors[0].identifier == ["https://orcid.org/456"]
    assert timdex_record.contributors[0].kind == "author"
    assert timdex_record.contributors[0].mit_affiliated is True
    assert timdex_record.dates[0].kind == "date of publication"
    assert timdex_record.dates[0].value == "2020-01-15"
    assert timdex_record.dates[1].kind == "dates collected"
    assert timdex_record.dates[1].note == "data collected every 3 days"
    assert timdex_record.dates[1].range.gt == "2019-01-01"
    assert timdex_record.dates[1].range.lt == "2019-06-30"
    assert timdex_record.identifiers[0].value == "123"
    assert timdex_record.identifiers[0].kind == "doi"
    assert timdex_record.notes[0].value == ["This book is awesome"]
    assert timdex_record.notes[0].kind == "opinion"
    assert timdex_record.publication_information == ["Version 1.0"]


def test_record_asdict_filters_empty_fields(timdex_record):
    assert timdex_record.asdict() == {
        "source": "A Cool Repository",
        "source_link": "https://example.com/item123",
        "timdex_record_id": "cool-repo:123",
        "title": "Some Data About Trees",
    }


def test_record_asdict_includes_all_fields(timdex_record):
    timdex_record.content_type = ["dataset"]
    timdex_record.contributors = [
        Contributor(
            value="Smith, Jane",
            affiliation=["MIT"],
            identifier=["https://orcid.org/456"],
            kind="author",
            mit_affiliated=True,
        )
    ]
    timdex_record.dates = [
        Date(kind="date of publication", value="2020-01-15"),
        Date(
            kind="dates collected",
            note="data collected every 3 days",
            range=Date_Range(gt="2019-01-01", lt="2019-06-30"),
        ),
    ]
    timdex_record.identifiers = [Identifier(value="123", kind="doi")]
    timdex_record.notes = [Note(value=["This book is awesome"], kind="opinion")]
    timdex_record.publication_information = ["Version 1.0"]
    assert timdex_record.asdict() == {
        "source": "A Cool Repository",
        "source_link": "https://example.com/item123",
        "timdex_record_id": "cool-repo:123",
        "title": "Some Data About Trees",
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
        "identifiers": [{"value": "123", "kind": "doi"}],
        "notes": [{"value": ["This book is awesome"], "kind": "opinion"}],
        "publication_information": ["Version 1.0"],
    }


def test_timdex_record_date_range_both_gt_and_gte(timdex_record):
    with raises(ValueError):
        timdex_record.dates = [
            Date(
                range=Date_Range(gt="2019-01-01", gte="2019-01-01", lt="2019-06-30"),
            )
        ]


def test_timdex_record_date_range_both_lt_and_lte(timdex_record):
    with raises(ValueError):
        timdex_record.dates = [
            Date(
                range=Date_Range(gt="2019-01-01", lt="2019-06-30", lte="2019-06-30"),
            )
        ]


def test_timdex_record_empty_list():
    with raises(ValueError):
        TimdexRecord(
            source="A Cool Repository",
            source_link="https://example.com/item123",
            timdex_record_id="cool-repo:123",
            title="Some Data About Trees",
            dates=[],
        )
