from transmogrifier.models import (
    Contributor,
    Date,
    Date_Range,
    Identifier,
    Note,
    TimdexRecord,
)

# TODO: add tests for helper functions


def test_timdex_record_required_fields_only():
    record = TimdexRecord(
        source="A Cool Repository",
        source_link="https://example.com/item123",
        timdex_record_id="cool-repo:123",
        title="Some Data About Trees",
    )
    assert record.source == "A Cool Repository"
    assert record.source_link == "https://example.com/item123"
    assert record.timdex_record_id == "cool-repo:123"
    assert record.title == "Some Data About Trees"
    assert record.content_type is None
    assert record.contributors is None
    assert record.dates is None
    assert record.identifiers is None
    assert record.notes is None
    assert record.publication_information is None


def test_timdex_record_required_subfields_only():
    record = TimdexRecord(
        source="A Cool Repository",
        source_link="https://example.com/item123",
        timdex_record_id="cool-repo:123",
        title="Some Data About Trees",
        contributors=[Contributor(value="Smith, Jane")],
        identifiers=[Identifier(value="123")],
        notes=[Note(value=["This book is awesome"])],
    )
    assert record.source == "A Cool Repository"
    assert record.source_link == "https://example.com/item123"
    assert record.timdex_record_id == "cool-repo:123"
    assert record.title == "Some Data About Trees"
    assert record.content_type is None
    assert record.contributors[0].value == "Smith, Jane"
    assert record.dates is None
    assert record.identifiers[0].value == "123"
    assert record.notes[0].value == ["This book is awesome"]
    assert record.publication_information is None


def test_timdex_record_all_fields_and_subfields():
    record = TimdexRecord(
        source="A Cool Repository",
        source_link="https://example.com/item123",
        timdex_record_id="cool-repo:123",
        title="Some Data About Trees",
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
        identifiers=[Identifier(value="123", kind="doi")],
        notes=[Note(value=["This book is awesome"], kind="opinion")],
        publication_information=["Version 1.0"],
    )
    assert record.source == "A Cool Repository"
    assert record.source_link == "https://example.com/item123"
    assert record.timdex_record_id == "cool-repo:123"
    assert record.title == "Some Data About Trees"
    assert record.content_type == ["dataset"]
    assert record.contributors[0].value == "Smith, Jane"
    assert record.contributors[0].affiliation == ["MIT"]
    assert record.contributors[0].identifier == ["https://orcid.org/456"]
    assert record.contributors[0].kind == "author"
    assert record.contributors[0].mit_affiliated is True
    assert record.dates[0].kind == "date of publication"
    assert record.dates[0].value == "2020-01-15"
    assert record.dates[1].kind == "dates collected"
    assert record.dates[1].note == "data collected every 3 days"
    assert record.dates[1].range.gt == "2019-01-01"
    assert record.dates[1].range.lt == "2019-06-30"
    assert record.identifiers[0].value == "123"
    assert record.identifiers[0].kind == "doi"
    assert record.notes[0].value == ["This book is awesome"]
    assert record.notes[0].kind == "opinion"
    assert record.publication_information == ["Version 1.0"]


def test_record_asdict_filters_empty_fields():
    record = TimdexRecord(
        source="A Cool Repository",
        source_link="https://example.com/item123",
        timdex_record_id="cool-repo:123",
        title="Some Data About Trees",
    )
    assert record.asdict() == {
        "source": "A Cool Repository",
        "source_link": "https://example.com/item123",
        "timdex_record_id": "cool-repo:123",
        "title": "Some Data About Trees",
    }


def test_record_asdict_includes_all_fields():
    record = TimdexRecord(
        source="A Cool Repository",
        source_link="https://example.com/item123",
        timdex_record_id="cool-repo:123",
        title="Some Data About Trees",
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
        identifiers=[Identifier(value="123", kind="doi")],
        notes=[Note(value=["This book is awesome"], kind="opinion")],
        publication_information=["Version 1.0"],
    )
    assert record.asdict() == {
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
