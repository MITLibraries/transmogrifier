from pytest import raises

from transmogrifier.models import Contributor, Date, Identifier, Note, TimdexRecord
from transmogrifier.sources.datacite import Datacite


def test_jpal_fixtures(datacite_jpal_records):
    output_records = Datacite(
        "jpal",
        "https://dataverse.harvard.edu/dataset.xhtml?persistentId=",
        "Abdul Latif Jameel Poverty Action Lab Dataverse",
        datacite_jpal_records,
    )
    assert len(list(output_records)) == 38


def test_datacite_full_record(datacite_record, datacite_jpal_record_full):
    datacite_record.input_records = datacite_jpal_record_full
    output_records = datacite_record
    for output_record in output_records:
        assert output_record == TimdexRecord(
            source="A Cool Repository",
            source_link="https://example.com/item123doi:10.7910/DVN/19PPE7",
            timdex_record_id="cool:doi:10.7910-DVN-19PPE7",
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


def test_datacite_minimal_record(datacite_record, datacite_jpal_record_minimal):
    datacite_record.input_records = datacite_jpal_record_minimal
    output_records = datacite_record
    for output_record in output_records:
        assert output_record == TimdexRecord(
            source="A Cool Repository",
            source_link="https://example.com/item123doi:10.7910/DVN/19PPE7",
            timdex_record_id="cool:doi:10.7910-DVN-19PPE7",
            title="The Impact of Maternal Literacy and Participation Programs",
            content_type=None,
            contributors=None,
            dates=None,
            identifiers=[Identifier(value="10.7910/DVN/19PPE7", kind="DOI")],
            notes=None,
            publication_information=None,
        )


def test_datacite_missing_required_field(
    datacite_record, datacite_jpal_record_missing_required_field
):
    with raises(ValueError):
        datacite_record.input_records = datacite_jpal_record_missing_required_field
        output_records = datacite_record
        for output_record in output_records:
            assert output_record


def test_datacite_multiple_titles(
    datacite_record, datacite_jpal_record_multiple_titles
):
    with raises(ValueError):
        datacite_record.input_records = datacite_jpal_record_multiple_titles
        output_records = datacite_record
        for output_record in output_records:
            assert output_record


def test_generate_name_identifier_url_orcid_scheme(
    datacite_record, datacite_jpal_record_orcid_name_identifier
):
    datacite_record.input_records = datacite_jpal_record_orcid_name_identifier
    output_records = datacite_record
    for output_record in output_records:
        assert output_record.contributors[0].identifier == [
            "https://orcid.org/0000-0000-0000-0000"
        ]


def test_generate_name_identifier_url_unknown_scheme(
    datacite_record, datacite_jpal_record_unknown_name_identifier
):
    datacite_record.input_records = datacite_jpal_record_unknown_name_identifier
    output_records = datacite_record
    for output_record in output_records:
        assert output_record.contributors[0].identifier == ["0000-0000-0000-0000"]
