import pytest

import transmogrifier.models as timdex


def test_timdex_record_required_fields_only(timdex_record_required_fields):
    assert timdex_record_required_fields.source == "A Cool Repository"
    assert timdex_record_required_fields.source_link == "https://example.com/123"
    assert timdex_record_required_fields.timdex_record_id == "cool-repo:123"
    assert timdex_record_required_fields.title == "Some Data About Trees"
    assert timdex_record_required_fields.alternate_titles is None
    assert timdex_record_required_fields.call_numbers is None
    assert timdex_record_required_fields.content_type is None
    assert timdex_record_required_fields.contents is None
    assert timdex_record_required_fields.contributors is None
    assert timdex_record_required_fields.dates is None
    assert timdex_record_required_fields.edition is None
    assert timdex_record_required_fields.file_formats is None
    assert timdex_record_required_fields.format is None
    assert timdex_record_required_fields.funding_information is None
    assert timdex_record_required_fields.holdings is None
    assert timdex_record_required_fields.identifiers is None
    assert timdex_record_required_fields.languages is None
    assert timdex_record_required_fields.links is None
    assert timdex_record_required_fields.literary_form is None
    assert timdex_record_required_fields.locations is None
    assert timdex_record_required_fields.notes is None
    assert timdex_record_required_fields.numbering is None
    assert timdex_record_required_fields.publication_frequency is None
    assert timdex_record_required_fields.physical_description is None
    assert timdex_record_required_fields.publishers is None
    assert timdex_record_required_fields.related_items is None
    assert timdex_record_required_fields.rights is None
    assert timdex_record_required_fields.subjects is None
    assert timdex_record_required_fields.summary is None


def test_timdex_record_required_subfields_only(timdex_record_required_fields):
    timdex_record_required_fields.contributors = [timdex.Contributor(value="Smith, Jane")]
    timdex_record_required_fields.identifiers = [timdex.Identifier(value="123")]
    timdex_record_required_fields.links = [
        timdex.Link(url="http://dx.doi.org/10.1007/978-94-017-0726-8")
    ]
    timdex_record_required_fields.notes = [timdex.Note(value=["This book is awesome"])]
    timdex_record_required_fields.alternate_titles = [
        timdex.AlternateTitle(value="Alt Title")
    ]
    timdex_record_required_fields.subjects = [timdex.Subject(value=["Stuff"])]
    assert timdex_record_required_fields.source == "A Cool Repository"
    assert timdex_record_required_fields.source_link == "https://example.com/123"
    assert timdex_record_required_fields.timdex_record_id == "cool-repo:123"
    assert timdex_record_required_fields.title == "Some Data About Trees"
    assert timdex_record_required_fields.alternate_titles[0].value == "Alt Title"
    assert timdex_record_required_fields.call_numbers is None
    assert timdex_record_required_fields.content_type is None
    assert timdex_record_required_fields.contents is None
    assert timdex_record_required_fields.contributors[0].value == "Smith, Jane"
    assert timdex_record_required_fields.dates is None
    assert timdex_record_required_fields.edition is None
    assert timdex_record_required_fields.file_formats is None
    assert timdex_record_required_fields.format is None
    assert timdex_record_required_fields.funding_information is None
    assert timdex_record_required_fields.holdings is None
    assert timdex_record_required_fields.identifiers[0].value == "123"
    assert timdex_record_required_fields.languages is None
    assert (
        timdex_record_required_fields.links[0].url
        == "http://dx.doi.org/10.1007/978-94-017-0726-8"
    )
    assert timdex_record_required_fields.literary_form is None
    assert timdex_record_required_fields.locations is None
    assert timdex_record_required_fields.notes[0].value == ["This book is awesome"]
    assert timdex_record_required_fields.numbering is None
    assert timdex_record_required_fields.physical_description is None
    assert timdex_record_required_fields.publication_frequency is None
    assert timdex_record_required_fields.publishers is None
    assert timdex_record_required_fields.rights is None
    assert timdex_record_required_fields.subjects[0].value == ["Stuff"]
    assert timdex_record_required_fields.summary is None


def test_timdex_record_all_fields_and_subfields(timdex_record_all_fields_and_subfields):
    assert (
        timdex_record_all_fields_and_subfields.citation
        == "Creator (PubYear): Title. Publisher. (resourceTypeGeneral). ID"
    )
    assert timdex_record_all_fields_and_subfields.source == "A Cool Repository"
    assert timdex_record_all_fields_and_subfields.source_link == "https://example.com/123"
    assert timdex_record_all_fields_and_subfields.timdex_record_id == "cool-repo:123"
    assert timdex_record_all_fields_and_subfields.title == "Some Data About Trees"
    assert timdex_record_all_fields_and_subfields.alternate_titles[0].value == "Alt title"
    assert (
        timdex_record_all_fields_and_subfields.alternate_titles[0].kind == "alternative"
    )
    assert timdex_record_all_fields_and_subfields.call_numbers == ["QC173.59.S65"]
    assert timdex_record_all_fields_and_subfields.content_type == ["dataset"]
    assert timdex_record_all_fields_and_subfields.contents == ["Chapter 1, Chapter 2"]
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
        == "http://awards.example/7689"
    )
    assert (
        timdex_record_all_fields_and_subfields.holdings[0].call_number == "QC173.59.S65"
    )
    assert timdex_record_all_fields_and_subfields.holdings[0].collection == "Stacks"
    assert timdex_record_all_fields_and_subfields.holdings[0].format == "Print volume"
    assert timdex_record_all_fields_and_subfields.holdings[0].location == "Hayden Library"
    assert timdex_record_all_fields_and_subfields.holdings[0].note == "Holdings note"
    assert timdex_record_all_fields_and_subfields.identifiers[0].value == "123"
    assert timdex_record_all_fields_and_subfields.identifiers[0].kind == "doi"
    assert timdex_record_all_fields_and_subfields.languages == ["en_US"]
    assert timdex_record_all_fields_and_subfields.links[0].kind == "SpringerLink"
    assert (
        timdex_record_all_fields_and_subfields.links[0].restrictions
        == "Touchstone authentication required for access"
    )
    assert (
        timdex_record_all_fields_and_subfields.links[0].text
        == "Direct access via SpringerLink"
    )
    assert (
        timdex_record_all_fields_and_subfields.links[0].url
        == "http://dx.doi.org/10.1007/978-94-017-0726-8"
    )
    assert timdex_record_all_fields_and_subfields.literary_form == "nonfiction"
    assert (
        timdex_record_all_fields_and_subfields.locations[0].value
        == "A point on the globe"
    )
    assert (
        timdex_record_all_fields_and_subfields.locations[0].kind
        == "Data was gathered here"
    )
    assert (
        timdex_record_all_fields_and_subfields.locations[0].geoshape
        == "BBOX(-77.025955, 38.942142)"
    )
    assert timdex_record_all_fields_and_subfields.notes[0].value == [
        "This book is awesome"
    ]
    assert timdex_record_all_fields_and_subfields.notes[0].kind == "opinion"
    assert (
        timdex_record_all_fields_and_subfields.numbering
        == "Began with v. 32, issue 1 (Jan./June 2005)."
    )
    assert (
        timdex_record_all_fields_and_subfields.physical_description
        == "1 online resource (1 sound file)"
    )
    assert timdex_record_all_fields_and_subfields.publication_frequency == ["Semiannual"]
    assert (
        timdex_record_all_fields_and_subfields.related_items[0].description
        == "This item is related to this other item"
    )
    assert (
        timdex_record_all_fields_and_subfields.related_items[0].item_type
        == "An item type"
    )
    assert (
        timdex_record_all_fields_and_subfields.related_items[0].relationship
        == "isReferencedBy"
    )
    assert (
        timdex_record_all_fields_and_subfields.related_items[0].uri
        == "http://doi.example/123"
    )
    assert (
        timdex_record_all_fields_and_subfields.rights[0].description
        == "People may use this"
    )
    assert timdex_record_all_fields_and_subfields.rights[0].kind == "Access rights"
    assert (
        timdex_record_all_fields_and_subfields.rights[0].uri == "http://rights.example/"
    )
    assert timdex_record_all_fields_and_subfields.subjects[0].value == ["Stuff"]
    assert timdex_record_all_fields_and_subfields.subjects[0].kind == "LCSH"
    assert timdex_record_all_fields_and_subfields.summary[0] == "This is data."


def test_record_asdict_filters_empty_fields(
    timdex_record_required_fields,
):
    assert timdex_record_required_fields.asdict() == {
        "source": "A Cool Repository",
        "source_link": "https://example.com/123",
        "timdex_record_id": "cool-repo:123",
        "title": "Some Data About Trees",
    }


def test_record_asdict_includes_all_fields(timdex_record_all_fields_and_subfields):
    assert timdex_record_all_fields_and_subfields.asdict() == {
        "citation": "Creator (PubYear): Title. Publisher. (resourceTypeGeneral). ID",
        "source": "A Cool Repository",
        "source_link": "https://example.com/123",
        "timdex_record_id": "cool-repo:123",
        "title": "Some Data About Trees",
        "alternate_titles": [{"kind": "alternative", "value": "Alt title"}],
        "content_type": ["dataset"],
        "call_numbers": ["QC173.59.S65"],
        "contents": ["Chapter 1, Chapter 2"],
        "contributors": [
            {
                "affiliation": ["MIT"],
                "identifier": ["https://orcid.org/456"],
                "kind": "author",
                "mit_affiliated": True,
                "value": "Smith, Jane",
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
                "award_uri": "http://awards.example/7689",
                "funder_identifier": "4356",
                "funder_identifier_type": "Crossref FunderID",
                "funder_name": "Funding Foundation",
            }
        ],
        "holdings": [
            {
                "call_number": "QC173.59.S65",
                "collection": "Stacks",
                "format": "Print volume",
                "location": "Hayden Library",
                "note": "Holdings note",
            }
        ],
        "identifiers": [{"value": "123", "kind": "doi"}],
        "languages": ["en_US"],
        "links": [
            {
                "kind": "SpringerLink",
                "restrictions": "Touchstone authentication required for access",
                "text": "Direct access via SpringerLink",
                "url": "http://dx.doi.org/10.1007/978-94-017-0726-8",
            }
        ],
        "literary_form": "nonfiction",
        "locations": [
            {
                "geoshape": "BBOX(-77.025955, 38.942142)",
                "kind": "Data was gathered here",
                "value": "A point on the globe",
            }
        ],
        "notes": [
            {
                "kind": "opinion",
                "value": ["This book is awesome"],
            }
        ],
        "numbering": "Began with v. 32, issue 1 (Jan./June 2005).",
        "physical_description": "1 online resource (1 sound file)",
        "publication_frequency": ["Semiannual"],
        "publishers": [{"name": "Publisher", "date": "2014", "location": "A place"}],
        "related_items": [
            {
                "description": "This item is related to this other item",
                "item_type": "An item type",
                "relationship": "isReferencedBy",
                "uri": "http://doi.example/123",
            }
        ],
        "rights": [
            {
                "description": "People may use this",
                "kind": "Access rights",
                "uri": "http://rights.example/",
            }
        ],
        "subjects": [{"kind": "LCSH", "value": ["Stuff"]}],
        "summary": ["This is data."],
    }


def test_timdex_record_date_range_both_gt_and_gte_raises_error(
    timdex_record_required_fields,
):
    with pytest.raises(
        ValueError,
        match="range may have a 'gt' or 'gte' value, but not both;",
    ):
        timdex_record_required_fields.dates = [
            timdex.Date(
                range=timdex.DateRange(
                    gt="2019-01-01", gte="2019-01-01", lt="2019-06-30"
                ),
            )
        ]


def test_timdex_record_date_range_both_lt_and_lte_raises_error(
    timdex_record_required_fields,
):
    with pytest.raises(
        ValueError, match="range may have a 'lt' or 'lte' value, but not both;"
    ):
        timdex_record_required_fields.dates = [
            timdex.Date(
                range=timdex.DateRange(
                    gt="2019-01-01", lt="2019-06-30", lte="2019-06-30"
                ),
            )
        ]


def test_timdex_record_empty_list_raises_error(timdex_record_required_fields):
    with pytest.raises(ValueError, match="'dates' cannot be an empty list"):
        timdex_record_required_fields.dates = []


def test_timdex_record_list_of_wrong_type_raises_error(timdex_record_required_fields):
    with pytest.raises(
        TypeError, match="'dates' must be <class 'transmogrifier.models.Date'>"
    ):
        timdex_record_required_fields.dates = ["test"]


def test_timdex_record_not_a_list_raises_error(timdex_record_required_fields):
    with pytest.raises(
        TypeError,
        match="'dates' must be <class 'list'>",
    ):
        timdex_record_required_fields.dates = "test"


def test_timdex_record_dedupe_alternate_titles(timdex_record_required_fields):
    timdex_record_required_fields.alternate_titles = [
        timdex.AlternateTitle(value="My Octopus Teacher"),
        timdex.AlternateTitle(value="My Octopus Teacher"),
    ]
    assert timdex_record_required_fields.alternate_titles == [
        timdex.AlternateTitle(value="My Octopus Teacher")
    ]


def test_timdex_record_dedupe_call_numbers(timdex_record_required_fields):
    timdex_record_required_fields.call_numbers = ["a", "a"]
    assert timdex_record_required_fields.call_numbers == ["a"]


def test_timdex_record_dedupe_content_type(timdex_record_required_fields):
    timdex_record_required_fields.content_type = ["thesis", "thesis"]
    assert timdex_record_required_fields.content_type == ["thesis"]


def test_timdex_record_dedupe_contents(timdex_record_required_fields):
    timdex_record_required_fields.contents = ["Chapter 1", "Chapter 1"]
    assert timdex_record_required_fields.contents == ["Chapter 1"]


def test_timdex_record_dedupe_contributors(timdex_record_required_fields):
    timdex_record_required_fields.contributors = [
        timdex.Contributor(
            value="Joe Hisaishi",
            affiliation=["Kunitachi College of Music"],
            kind="Composer",
        ),
        timdex.Contributor(
            value="Joe Hisaishi",
            affiliation=["Kunitachi College of Music"],
            kind="Composer",
        ),
    ]
    assert timdex_record_required_fields.contributors == [
        timdex.Contributor(
            value="Joe Hisaishi",
            affiliation=["Kunitachi College of Music"],
            kind="Composer",
        )
    ]


def test_timdex_record_dedupe_dates(timdex_record_required_fields):
    timdex_record_required_fields.dates = [
        timdex.Date(value="2022-01-01", kind="Publication date"),
        timdex.Date(value="2022-01-01", kind="Publication date"),
        timdex.Date(
            range=timdex.DateRange(gt="2019-01-01", lt="2019-06-30"),
        ),
        timdex.Date(
            range=timdex.DateRange(gt="2019-01-01", lt="2019-06-30"),
        ),
    ]
    assert timdex_record_required_fields.dates == [
        timdex.Date(value="2022-01-01", kind="Publication date"),
        timdex.Date(
            range=timdex.DateRange(gt="2019-01-01", lt="2019-06-30"),
        ),
    ]


def test_timdex_record_dedupe_file_formats(timdex_record_required_fields):
    timdex_record_required_fields.file_formats = [
        "application/pdf",
        "application/pdf",
    ]
    assert timdex_record_required_fields.file_formats == ["application/pdf"]


def test_timdex_record_dedupe_funding_information(timdex_record_required_fields):
    timdex_record_required_fields.funding_information = [
        timdex.Funder(funder_name="NPR Foundation"),
        timdex.Funder(funder_name="NPR Foundation"),
    ]
    assert timdex_record_required_fields.funding_information == [
        timdex.Funder(funder_name="NPR Foundation")
    ]


def test_timdex_record_dedupe_holdings(timdex_record_required_fields):
    timdex_record_required_fields.holdings = [
        timdex.Holding(
            call_number="PL2687.L8.A28 1994",
            collection="Stacks",
            format="Print volume",
            location="Hayden Library",
        ),
        timdex.Holding(
            call_number="PL2687.L8.A28 1994",
            collection="Stacks",
            format="Print volume",
            location="Hayden Library",
        ),
    ]
    assert timdex_record_required_fields.holdings == [
        timdex.Holding(
            call_number="PL2687.L8.A28 1994",
            collection="Stacks",
            format="Print volume",
            location="Hayden Library",
        )
    ]


def test_timdex_record_dedupe_identifiers(timdex_record_required_fields):
    timdex_record_required_fields.identifiers = [
        timdex.Identifier(value="9781250185969. hardcover", kind="ISBN"),
        timdex.Identifier(value="9781250185969. hardcover", kind="ISBN"),
    ]
    assert timdex_record_required_fields.identifiers == [
        timdex.Identifier(value="9781250185969. hardcover", kind="ISBN")
    ]


def test_timdex_record_dedupe_languages(timdex_record_required_fields):
    timdex_record_required_fields.languages = ["Spanish", "Spanish"]
    assert timdex_record_required_fields.languages == ["Spanish"]


def test_timdex_record_dedupe_links(timdex_record_required_fields):
    timdex_record_required_fields.links = [
        timdex.Link(
            url="https://geodata.libraries.mit.edu/record/gismit"
            ":GISPORTAL_GISOWNER01_BOSTONWATER95",
            kind="Website",
            text="Website",
        ),
        timdex.Link(
            url="https://geodata.libraries.mit.edu/record/gismit"
            ":GISPORTAL_GISOWNER01_BOSTONWATER95",
            kind="Website",
            text="Website",
        ),
    ]
    assert timdex_record_required_fields.links == [
        timdex.Link(
            url="https://geodata.libraries.mit.edu/record/gismit"
            ":GISPORTAL_GISOWNER01_BOSTONWATER95",
            kind="Website",
            text="Website",
        )
    ]


def test_timdex_record_dedupe_locations(timdex_record_required_fields):
    timdex_record_required_fields.locations = [
        timdex.Location(value="One Place", kind="Place of Publication"),
        timdex.Location(value="One Place", kind="Place of Publication"),
    ]
    assert timdex_record_required_fields.locations == [
        timdex.Location(value="One Place", kind="Place of Publication")
    ]


def test_timdex_record_dedupe_notes(timdex_record_required_fields):
    timdex_record_required_fields.notes = [
        timdex.Note(value=["Survey Data"], kind="Datacite resource type"),
        timdex.Note(value=["Survey Data"], kind="Datacite resource type"),
    ]
    assert timdex_record_required_fields.notes == [
        timdex.Note(value=["Survey Data"], kind="Datacite resource type"),
    ]


def test_timdex_record_dedupe_publication_frequency(timdex_record_required_fields):
    timdex_record_required_fields.publication_frequency = [
        "Three times a year",
        "Three times a year",
    ]
    assert timdex_record_required_fields.publication_frequency == ["Three times a year"]


def test_timdex_record_dedupe_publishers(timdex_record_required_fields):
    timdex_record_required_fields.publishers = [
        timdex.Publisher(name="Harvard Dataverse"),
        timdex.Publisher(name="Harvard Dataverse"),
    ]
    assert timdex_record_required_fields.publishers == [
        timdex.Publisher(name="Harvard Dataverse")
    ]


def test_timdex_record_dedupe_related_items(timdex_record_required_fields):
    timdex_record_required_fields.related_items = [
        timdex.RelatedItem(description="Nature Communications", relationship="host"),
        timdex.RelatedItem(description="Nature Communications", relationship="host"),
    ]
    assert timdex_record_required_fields.related_items == [
        timdex.RelatedItem(description="Nature Communications", relationship="host")
    ]


def test_timdex_record_dedupe_rights(timdex_record_required_fields):
    timdex_record_required_fields.rights = [
        timdex.Rights(description="MIT authentication required", kind="Access to files"),
        timdex.Rights(description="MIT authentication required", kind="Access to files"),
    ]
    assert timdex_record_required_fields.rights == [
        timdex.Rights(description="MIT authentication required", kind="Access to files")
    ]


def test_timdex_record_dedupe_subjects(timdex_record_required_fields):
    timdex_record_required_fields.subjects = [
        timdex.Subject(
            value=["Social Sciences", "Educational materials"],
            kind="Subject scheme not provided",
        ),
        timdex.Subject(
            value=["Social Sciences", "Educational materials"],
            kind="Subject scheme not provided",
        ),
    ]
    assert timdex_record_required_fields.subjects == [
        timdex.Subject(
            value=["Social Sciences", "Educational materials"],
            kind="Subject scheme not provided",
        )
    ]


def test_timdex_record_dedupe_summary(timdex_record_required_fields):
    timdex_record_required_fields.summary = [
        "Mitochondria is the powerhouse of the cell.",
        "Mitochondria is the powerhouse of the cell.",
    ]
    assert timdex_record_required_fields.summary == [
        "Mitochondria is the powerhouse of the cell."
    ]
