from pytest import raises

from transmogrifier.models import (
    AlternateTitle,
    Contributor,
    Date,
    Date_Range,
    Funder,
    Identifier,
    Location,
    Note,
    RelatedItem,
    Rights,
    Subject,
    TimdexRecord,
)
from transmogrifier.sources.datacite import Datacite


def test_datacite_iterates_through_all_records(datacite_jpal_records):
    output_records = Datacite(
        "jpal",
        "https://dataverse.harvard.edu/dataset.xhtml?persistentId=",
        "Abdul Latif Jameel Poverty Action Lab Dataverse",
        datacite_jpal_records,
    )
    assert len(list(output_records)) == 38


def test_datacite_record_all_fields(
    datacite_record_partial, datacite_jpal_record_all_fields
):
    output_records = datacite_record_partial(
        input_records=datacite_jpal_record_all_fields
    )
    assert next(output_records) == TimdexRecord(
        citation=(
            "Banerji, Rukmini; Berry, James; Shotland, Marc; Banerji, Rukmini "
            "(2017): The Impact of Maternal Literacy and Participation Programs. Harvard "
            "Dataverse. https://example.com/doi:10.7910/DVN/19PPE7"
        ),
        source="A Cool Repository",
        source_link="https://example.com/doi:10.7910/DVN/19PPE7",
        timdex_record_id="cool-repo:doi:10.7910-DVN-19PPE7",
        title="The Impact of Maternal Literacy and Participation Programs",
        alternate_titles=[
            AlternateTitle(value="An Alternative Title", kind="AlternativeTitle"),
            AlternateTitle(value="Baseline Data", kind="Subtitle"),
        ],
        content_type=["Dataset"],
        contributors=[
            Contributor(
                value="Banerji, Rukmini",
                affiliation=["Pratham and ASER Centre"],
                identifier=["https://orcid.org/0000-0000-0000-0000"],
                kind="Creator",
                mit_affiliated=None,
            ),
            Contributor(
                value="Berry, James",
                affiliation=["University of Delaware"],
                identifier=None,
                kind="Creator",
                mit_affiliated=None,
            ),
            Contributor(
                value="Shotland, Marc",
                affiliation=["Abdul Latif Jameel Poverty Action Lab"],
                identifier=None,
                kind="Creator",
                mit_affiliated=None,
            ),
            Contributor(
                value="Banerji, Rukmini",
                affiliation=["Pratham and ASER Centre"],
                identifier=["https://orcid.org/0000-0000-0000-0000"],
                kind="ContactPerson",
                mit_affiliated=None,
            ),
        ],
        dates=[
            Date(kind="Publication date", note=None, range=None, value="2017"),
            Date(kind="Submitted", note=None, range=None, value="2017-02-27"),
            Date(
                kind="Updated",
                note="This was updated on this date",
                range=None,
                value="2019-06-24",
            ),
            Date(
                kind="Collected",
                note=None,
                range=Date_Range(gt=None, gte="2007-01-0", lt=None, lte="2007-02-28"),
                value=None,
            ),
        ],
        edition="1.2",
        file_formats=[
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            "application/pdf",
            "application/pdf",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            "application/pdf",
            "application/x-stata-syntax",
            "application/x-stata",
            "application/x-stata",
            "application/zip",
            "application/pdf",
            "application/pdf",
        ],
        format="electronic resource",
        funding_information=[
            Funder(
                funder_name="3ie, Nike Foundation",
                funder_identifier="0987",
                funder_identifier_type="Crossref FunderID",
                award_number="OW1/1012 (3ie)",
                award_uri="http://awards.example/7689",
            )
        ],
        identifiers=[Identifier(value="10.7910/DVN/19PPE7", kind="DOI")],
        locations=[Location(value="A point on the globe")],
        languages=["en_US"],
        notes=[
            Note(value=["Survey Data"], kind="Datacite resource type"),
            Note(value=["Stata, 13"], kind="TechnicalInfo"),
        ],
        publication_information=["Harvard Dataverse"],
        related_items=[
            RelatedItem(
                relationship="IsCitedBy",
                uri="https://doi.org/10.1257/app.20150390",
            )
        ],
        rights=[
            Rights(uri="info:eu-repo/semantics/openAccess"),
            Rights(
                description="CC0 1.0",
                uri="http://creativecommons.org/publicdomain/zero/1.0",
            ),
        ],
        subjects=[
            Subject(value=["Social Sciences"], kind=None),
            Subject(
                value=["Adult education, education inputs, field experiments"],
                kind="LCSH",
            ),
        ],
        summary=[
            "Using a randomized field experiment in India, we evaluate the effectiveness "
            "of adult literacy and parental involvement interventions in improving "
            "children's learning. Households were assigned to receive either adult "
            "literacy (language and math) classes for mothers, training for mothers on "
            "how to enhance their children's learning at home, or a combination of the "
            "two programs. All three interventions had significant but modest impacts on "
            "childrens math scores. The interventions also increased mothers' test scores"
            " in both language and math, as well as a range of other outcomes reflecting "
            "greater involvement of mothers in their children's education."
        ],
    )


def test_datacite_required_fields_record(
    datacite_record_partial, datacite_jpal_record_required_fields
):
    output_records = datacite_record_partial(
        input_records=datacite_jpal_record_required_fields
    )
    assert next(output_records) == TimdexRecord(
        citation=(
            "The Impact of Maternal Literacy and Participation Programs. "
            "https://example.com/doi:10.7910/DVN/19PPE7"
        ),
        source="A Cool Repository",
        source_link="https://example.com/doi:10.7910/DVN/19PPE7",
        timdex_record_id="cool-repo:doi:10.7910-DVN-19PPE7",
        title="The Impact of Maternal Literacy and Participation Programs",
        format="electronic resource",
        alternate_titles=None,
        content_type=None,
        contributors=None,
        dates=None,
        edition=None,
        file_formats=None,
        funding_information=None,
        identifiers=[Identifier(value="10.7910/DVN/19PPE7", kind="DOI")],
        locations=None,
        notes=None,
        publication_information=None,
        related_items=None,
        rights=None,
        subjects=None,
        summary=None,
    )


def test_datacite_missing_required_fields_raises_warning(
    caplog,
    datacite_record_partial,
    datacite_jpal_record_missing_required_fields_warning,
):
    output_records = datacite_record_partial(
        input_records=datacite_jpal_record_missing_required_fields_warning
    )
    next(output_records)

    assert (
        "Datacite record doi:10.7910/DVN/19PPE7 missing required Datacite field "
        "resourceType"
    ) in caplog.text

    assert (
        "Datacite record doi:10.7910/DVN/19PPE7 missing required Datacite field "
        "publicationYear"
    ) in caplog.text
    assert (
        "Datacite record doi:10.7910/DVN/19PPE7 missing required Datacite attribute "
        "@descriptionType"
    ) in caplog.text
    assert (
        "Datacite record doi:10.7910/DVN/19PPE7 missing required Datacite field publisher"
    ) in caplog.text


def test_datacite_missing_required_field_raises_error(
    datacite_record_partial, datacite_jpal_record_missing_required_field_error
):
    with raises(ValueError):
        output_records = datacite_record_partial(
            input_records=datacite_jpal_record_missing_required_field_error
        )
        next(output_records)


def test_datacite_multiple_titles_raises_error(
    datacite_record_partial, datacite_jpal_record_multiple_titles
):
    with raises(ValueError):
        output_records = datacite_record_partial(
            input_records=datacite_jpal_record_multiple_titles
        )
        next(output_records)


def test_generate_name_identifier_url_orcid_scheme(
    datacite_record_partial, datacite_jpal_record_orcid_name_identifier
):
    output_records = datacite_record_partial(
        input_records=datacite_jpal_record_orcid_name_identifier
    )
    assert next(output_records).contributors[0].identifier == [
        "https://orcid.org/0000-0000-0000-0000"
    ]


def test_generate_name_identifier_url_unknown_scheme(
    datacite_record_partial, datacite_jpal_record_unknown_name_identifier
):
    output_records = datacite_record_partial(
        input_records=datacite_jpal_record_unknown_name_identifier
    )
    assert next(output_records).contributors[0].identifier == ["0000-0000-0000-0000"]


def test_generate_related_item_identifier_url_doi_type(
    datacite_record_partial, datacite_jpal_record_related_item_identifier_doi_type
):
    output_records = datacite_record_partial(
        input_records=datacite_jpal_record_related_item_identifier_doi_type
    )
    assert next(output_records).related_items[0].uri == "https://doi.org/0000.0000"


def test_generate_related_item_identifier_url_unknown_type(
    datacite_record_partial, datacite_jpal_record_related_item_identifier_unknown_type
):
    output_records = datacite_record_partial(
        input_records=datacite_jpal_record_related_item_identifier_unknown_type
    )
    assert next(output_records).related_items[0].uri == "0000.0000"
