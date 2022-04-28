from pytest import raises

from transmogrifier.models import Contributor, Date, Identifier, Note, TimdexRecord
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
        source="A Cool Repository",
        source_link="https://example.com/item123doi:10.7910/DVN/19PPE7",
        timdex_record_id="cool-repo:doi:10.7910-DVN-19PPE7",
        title="The Impact of Maternal Literacy and Participation Programs",
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
        dates=[Date(kind="Publication date", note=None, range=None, value="2017")],
        identifiers=[Identifier(value="10.7910/DVN/19PPE7", kind="DOI")],
        notes=[Note(value=["Survey Data"], kind="Datacite resource type")],
        publication_information=["Harvard Dataverse"],
    )


def test_datacite_required_fields_record(
    datacite_record_partial, datacite_jpal_record_required_fields
):
    output_records = datacite_record_partial(
        input_records=datacite_jpal_record_required_fields
    )
    assert next(output_records) == TimdexRecord(
        source="A Cool Repository",
        source_link="https://example.com/item123doi:10.7910/DVN/19PPE7",
        timdex_record_id="cool-repo:doi:10.7910-DVN-19PPE7",
        title="The Impact of Maternal Literacy and Participation Programs",
        content_type=None,
        contributors=None,
        dates=None,
        identifiers=[Identifier(value="10.7910/DVN/19PPE7", kind="DOI")],
        notes=None,
        publication_information=None,
    )


def test_datacite_missing_required_field(
    datacite_record_partial, datacite_jpal_record_missing_required_field
):
    with raises(ValueError):
        output_records = datacite_record_partial(
            input_records=datacite_jpal_record_missing_required_field
        )
        assert next(output_records)


def test_datacite_multiple_titles(
    datacite_record_partial, datacite_jpal_record_multiple_titles
):
    with raises(ValueError):
        output_records = datacite_record_partial(
            input_records=datacite_jpal_record_multiple_titles
        )
        assert next(output_records)


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
