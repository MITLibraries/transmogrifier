from transmogrifier.helpers import parse_xml_records
from transmogrifier.sources.datacite import Datacite


# TODO: add tests for expected data issues:
# missing required Datacite fields raises error
# all fields transformed successfully
# repeatable fields transformed successfully


def test_jpal_fixtures():
    input_records = parse_xml_records("tests/fixtures/datacite_jpal_records.xml")
    output_records = Datacite(
        "jpal",
        "https://dataverse.harvard.edu/dataset.xhtml?persistentId=",
        "Abdul Latif Jameel Poverty Action Lab Dataverse",
        input_records,
    )
    assert len(list(output_records)) == 38


# TODO: add tests for generate_name_identifier_url expected cases
