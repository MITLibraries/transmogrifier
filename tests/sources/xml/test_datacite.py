from bs4 import BeautifulSoup

from transmogrifier.models import (
    AlternateTitle,
    Contributor,
    Date,
    DateRange,
    Funder,
    Identifier,
    Link,
    Location,
    Note,
    Publisher,
    RelatedItem,
    Rights,
    Subject,
    TimdexRecord,
)
from transmogrifier.sources.xml.datacite import Datacite


def create_datacite_source_record_stub(xml_insert: str = "") -> BeautifulSoup:
    xml_string = f"""
        <records>
         <record xmlns="http://www.openarchives.org/OAI/2.0/"
         xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
          <header>
            <identifier>abc123</identifier>
          <header>
          <metadata>
           <resource xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
           xmlns="http://datacite.org/schema/kernel-4"
           xsi:schemaLocation="http://datacite.org/schema/kernel-4
           http://schema.datacite.org/meta/kernel-4.1/metadata.xsd">
           {xml_insert}
           </resource>
          </metadata>
         </record>
        </records>
        """
    return BeautifulSoup(xml_string, "xml")


def test_datacite_transform_with_all_fields_transforms_correctly(
    datacite_record_all_fields,
):
    assert next(datacite_record_all_fields) == TimdexRecord(
        citation=(
            "Banerji, Rukmini, Berry, James, Shotland, Marc "
            "(2017): The Impact of Maternal Literacy and Participation Programs. Harvard "
            "Dataverse. Dataset. https://example.com/doi:10.7910/DVN/19PPE7"
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
            ),
            Contributor(
                value="Berry, James",
                affiliation=["University of Delaware"],
                identifier=["0000-0000-0000-0001"],
                kind="Creator",
            ),
            Contributor(
                value="Shotland, Marc",
                affiliation=["Abdul Latif Jameel Poverty Action Lab"],
                identifier=["0000-0000-0000-0002"],
                kind="Creator",
            ),
            Contributor(
                value="Banerji, Rukmini",
                affiliation=["Pratham and ASER Centre"],
                identifier=["https://orcid.org/0000-0000-0000-0000"],
                kind="ContactPerson",
            ),
        ],
        dates=[
            Date(kind="Publication date", value="2017"),
            Date(kind="Submitted", value="2017-02-27"),
            Date(
                kind="Updated",
                note="This was updated on this date",
                value="2019-06-24",
            ),
            Date(
                kind="Collected",
                range=DateRange(gte="2007-01-01", lte="2007-02-28"),
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
                award_number="OW1/1012 (3ie)",
                award_uri="http://awards.example/7689",
            )
        ],
        identifiers=[
            Identifier(value="10.7910/DVN/19PPE7", kind="DOI"),
            Identifier(value="https://zenodo.org/record/5524465", kind="url"),
            Identifier(value="1234567.5524464", kind="IsIdenticalTo"),
        ],
        locations=[Location(value="A point on the globe")],
        links=[
            Link(
                url="https://example.com/doi:10.7910/DVN/19PPE7",
                kind="Digital object URL",
                text="Digital object URL",
            )
        ],
        languages=["en_US"],
        notes=[
            Note(value=["Survey Data"], kind="Datacite resource type"),
            Note(value=["Stata, 13"], kind="TechnicalInfo"),
        ],
        publishers=[Publisher(name="Harvard Dataverse")],
        related_items=[
            RelatedItem(
                relationship="IsCitedBy",
                uri="https://doi.org/10.1257/app.20150390",
            ),
            RelatedItem(
                relationship="IsVersionOf",
                uri="10.5281/zenodo.5524464",
            ),
            RelatedItem(
                relationship="Other",
                uri="1234567.5524464",
            ),
            RelatedItem(
                relationship="IsPartOf",
                uri="https://zenodo.org/communities/astronomy-general",
            ),
        ],
        rights=[
            Rights(uri="info:eu-repo/semantics/openAccess"),
            Rights(
                description="CC0 1.0",
                uri="http://creativecommons.org/publicdomain/zero/1.0",
            ),
        ],
        subjects=[
            Subject(
                value=["Social Sciences", "Educational materials"],
                kind="Subject scheme not provided",
            ),
            Subject(
                value=[
                    "Adult education, education inputs, field experiments",
                    "Education",
                ],
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


def test_datacite_transform_missing_required_datacite_fields_logs_warning(caplog):
    source_records = Datacite.parse_source_file(
        "tests/fixtures/datacite/datacite_record_missing_datacite_required_fields.xml"
    )
    output_records = Datacite("cool-repo", source_records)
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


def test_datacite_transform_with_optional_fields_blank_transforms_correctly():
    source_records = Datacite.parse_source_file(
        "tests/fixtures/datacite/datacite_record_optional_fields_blank.xml"
    )
    output_records = Datacite("cool-repo", source_records)
    assert next(output_records) == TimdexRecord(
        citation=("Title not provided. https://example.com/doi:10.7910/DVN/19PPE7"),
        source="A Cool Repository",
        source_link="https://example.com/doi:10.7910/DVN/19PPE7",
        timdex_record_id="cool-repo:doi:10.7910-DVN-19PPE7",
        title="Title not provided",
        format="electronic resource",
        links=[
            Link(
                url="https://example.com/doi:10.7910/DVN/19PPE7",
                kind="Digital object URL",
                text="Digital object URL",
            )
        ],
        content_type=["Not specified"],
    )


def test_datacite_transform_with_optional_fields_missing_transforms_correctly():
    source_records = Datacite.parse_source_file(
        "tests/fixtures/datacite/datacite_record_optional_fields_missing.xml"
    )
    output_records = Datacite("cool-repo", source_records)
    assert next(output_records) == TimdexRecord(
        citation=("Title not provided. https://example.com/doi:10.7910/DVN/19PPE7"),
        source="A Cool Repository",
        source_link="https://example.com/doi:10.7910/DVN/19PPE7",
        timdex_record_id="cool-repo:doi:10.7910-DVN-19PPE7",
        title="Title not provided",
        format="electronic resource",
        links=[
            Link(
                url="https://example.com/doi:10.7910/DVN/19PPE7",
                kind="Digital object URL",
                text="Digital object URL",
            )
        ],
        content_type=["Not specified"],
    )


def test_datacite_with_attribute_and_subfield_variations_transforms_correctly():
    source_records = Datacite.parse_source_file(
        "tests/fixtures/datacite/datacite_record_attribute_and_subfield_variations.xml"
    )
    output_records = Datacite("cool-repo", source_records)
    assert next(output_records) == TimdexRecord(
        citation=(
            "Creator, No affiliation no identifier, Creator, Blank affiliation blank "
            "identifier, Creator, Identifier no scheme, Creator, Identifier blank "
            "scheme, Creator, No identifier with identifier scheme. Title with Blank "
            "titleType. https://example.com/doi:10.7910/DVN/19PPE7"
        ),
        source="A Cool Repository",
        source_link="https://example.com/doi:10.7910/DVN/19PPE7",
        timdex_record_id="cool-repo:doi:10.7910-DVN-19PPE7",
        title="Title with Blank titleType",
        alternate_titles=[AlternateTitle(value="A Second Title with Blank titleType")],
        content_type=["Not specified"],
        contributors=[
            Contributor(value="Creator, No affiliation no identifier", kind="Creator"),
            Contributor(
                value="Creator, Blank affiliation blank identifier", kind="Creator"
            ),
            Contributor(
                value="Creator, Identifier no scheme",
                identifier=["0000-0000-0000-0000"],
                kind="Creator",
            ),
            Contributor(
                value="Creator, Identifier blank scheme",
                identifier=["0000-0000-0000-0000"],
                kind="Creator",
            ),
            Contributor(
                value="Creator, No identifier with identifier scheme",
                kind="Creator",
            ),
            Contributor(
                value="Contributor, No affiliation no identifier no type",
                kind="Not specified",
            ),
            Contributor(
                value="Contributor, Blank affiliation blank identifier blank type",
                kind="Not specified",
            ),
            Contributor(
                value="Contributor, Identifier no scheme",
                identifier=["0000-0000-0000-0000"],
                kind="Not specified",
            ),
            Contributor(
                value="Contributor, Identifier blank scheme",
                identifier=["0000-0000-0000-0000"],
                kind="Not specified",
            ),
            Contributor(
                value="Contributor, No identifier with identifier scheme",
                kind="Not specified",
            ),
        ],
        dates=[
            Date(value="2020-01-01"),
            Date(note="OTHER"),
            Date(value="2020-01-02"),
        ],
        format="electronic resource",
        funding_information=[
            Funder(funder_name="Funder name no identifier no award"),
            Funder(funder_name="Funder name blank identifier blank award"),
            Funder(funder_identifier="Funder identifier no type"),
            Funder(funder_identifier="Funder identifier blank type"),
            Funder(award_number="Funder award no uri"),
            Funder(award_number="Funder award blank uri"),
            Funder(award_uri="Funder award uri without string"),
        ],
        identifiers=[
            Identifier(value="ID-blank-type", kind="Not specified"),
            Identifier(value="alternate-ID-no-type", kind="Not specified"),
            Identifier(value="alternate-ID-blank-type", kind="Not specified"),
            Identifier(
                value="Related ID relationType IsIdenticalTo no relationIdentifierType",
                kind="IsIdenticalTo",
            ),
            Identifier(
                value="Related ID relationType IsIdenticalTo blank "
                "relationIdentifierType",
                kind="IsIdenticalTo",
            ),
        ],
        links=[
            Link(
                url="https://example.com/doi:10.7910/DVN/19PPE7",
                kind="Digital object URL",
                text="Digital object URL",
            )
        ],
        notes=[
            Note(value=["Description no type"]),
            Note(value=["Description blank type"]),
        ],
        related_items=[
            RelatedItem(
                relationship="Not specified",
                uri="Related ID no relationType no relatedIdentifierType",
            ),
            RelatedItem(
                relationship="Not specified",
                uri="Related ID blank relationType blank relatedIdentifierType",
            ),
        ],
        rights=[
            Rights(description="Right no URI"),
            Rights(description="Right blank URI"),
            Rights(uri="Right URI without string"),
        ],
        subjects=[Subject(value=["Subject One"], kind="Subject scheme not provided")],
    )


def test_get_alternate_titles_success():
    source_record = create_datacite_source_record_stub(
        """
        <titles>
         <title>The Impact of Maternal Literacy and Participation Programs</title>
         <title titleType="AlternativeTitle">An Alternative Title</title>
         <title titleType="Subtitle">Baseline Data</title>
        </titles>
        """
    )
    assert Datacite.get_alternate_titles(source_record) == [
        AlternateTitle(value="An Alternative Title", kind="AlternativeTitle"),
        AlternateTitle(value="Baseline Data", kind="Subtitle"),
    ]


def test_get_alternate_titles_transforms_correctly_if_fields_blank():
    source_record = create_datacite_source_record_stub(
        '<titles><title titleType="AlternativeTitle"></title></titles>'
    )
    assert Datacite.get_alternate_titles(source_record) is None


def test_get_alternate_titles_transforms_correctly_if_fields_missing():
    source_record = create_datacite_source_record_stub()
    assert Datacite.get_alternate_titles(source_record) is None


def test_get_content_type_success():
    source_record = create_datacite_source_record_stub(
        """
        <resourceType resourceTypeGeneral="Dataset">Survey Data</resourceType>
        """
    )
    assert Datacite.get_content_type(source_record) == ["Dataset"]


def test_get_content_type_transforms_correctly_if_fields_blank():
    source_record = create_datacite_source_record_stub(
        """
        <resourceType resourceTypeGeneral=""></resourceType>
        """
    )
    assert Datacite.get_content_type(source_record) is None


def test_get_content_type_transforms_correctly_if_fields_missing():
    source_record = create_datacite_source_record_stub()
    assert Datacite.get_content_type(source_record) is None


def test_get_contributors_success():
    source_record = create_datacite_source_record_stub(
        """
        <creators>
         <creator>
          <creatorName nameType="Personal">Banerji, Rukmini</creatorName>
          <givenName>Rukmini</givenName>
          <familyName>Banerji</familyName>
          <affiliation>Pratham and ASER Centre</affiliation>
        <nameIdentifier nameIdentifierScheme="ORCID">0000-0000-0000-0000</nameIdentifier>
         </creator>
         <creator>
          <creatorName nameType="Personal">Berry, James</creatorName>
          <givenName>James</givenName>
          <familyName>Berry</familyName>
          <affiliation>University of Delaware</affiliation>
          <nameIdentifier nameIdentifierScheme="TREX">0000-0000-0000-0001</nameIdentifier>
          </creator>
         <creator>
          <creatorName nameType="Personal">Shotland, Marc</creatorName>
          <givenName>Marc</givenName>
          <familyName>Shotland</familyName>
          <affiliation>Abdul Latif Jameel Poverty Action Lab</affiliation>
          <nameIdentifier>0000-0000-0000-0002</nameIdentifier>
         </creator>
         </creators>
        <contributors>
         <contributor contributorType="ContactPerson">
          <contributorName nameType="Personal">Banerji, Rukmini</contributorName>
          <givenName>Rukmini</givenName>
          <familyName>Banerji</familyName>
        <nameIdentifier nameIdentifierScheme="ORCID">0000-0000-0000-0000</nameIdentifier>
          <affiliation>Pratham and ASER Centre</affiliation>
         </contributor>
        </contributors>
        """
    )
    assert Datacite.get_contributors(source_record) == [
        Contributor(
            value="Banerji, Rukmini",
            affiliation=["Pratham and ASER Centre"],
            identifier=["https://orcid.org/0000-0000-0000-0000"],
            kind="Creator",
        ),
        Contributor(
            value="Berry, James",
            affiliation=["University of Delaware"],
            identifier=["0000-0000-0000-0001"],
            kind="Creator",
        ),
        Contributor(
            value="Shotland, Marc",
            affiliation=["Abdul Latif Jameel Poverty Action Lab"],
            identifier=["0000-0000-0000-0002"],
            kind="Creator",
        ),
        Contributor(
            value="Banerji, Rukmini",
            affiliation=["Pratham and ASER Centre"],
            identifier=["https://orcid.org/0000-0000-0000-0000"],
            kind="ContactPerson",
        ),
    ]


def test_get_contributors_transforms_correctly_if_fields_blank():
    source_record = create_datacite_source_record_stub(
        """
        <creators>
         <creator />
        <contributors>
         <contributor />
        </contributors>
        """
    )
    assert Datacite.get_contributors(source_record) is None


def test_get_contributors_transforms_correctly_if_fields_missing():
    source_record = create_datacite_source_record_stub()
    assert Datacite.get_contributors(source_record) is None


def test_get_dates_success():
    source_record = create_datacite_source_record_stub(
        """
        <publicationYear>2017</publicationYear>
        <dates>
         <date dateType="Submitted">2017-02-27</date>
         <date dateType="Updated"
         dateInformation="This was updated on this date">2019-06-24</date>
         <date dateType="Collected">2007-01-01/2007-02-28</date>
        </dates>
        """
    )
    assert Datacite.get_dates(source_record) == [
        Date(kind="Publication date", value="2017"),
        Date(kind="Submitted", value="2017-02-27"),
        Date(kind="Updated", note="This was updated on this date", value="2019-06-24"),
        Date(
            kind="Collected",
            range=DateRange(gte="2007-01-01", lte="2007-02-28"),
        ),
    ]


def test_get_dates_transforms_correctly_if_fields_blank():
    source_record = create_datacite_source_record_stub(
        """
        <publicationYear />
        <dates>
         <date />
        </dates>
        """
    )
    assert Datacite.get_dates(source_record) is None


def test_get_dates_transforms_correctly_if_fields_missing():
    source_record = create_datacite_source_record_stub()
    assert Datacite.get_dates(source_record) is None


def test_get_edition_success():
    source_record = create_datacite_source_record_stub("<version>1.2</version>")
    assert Datacite.get_edition(source_record) == "1.2"


def test_get_edition_transforms_correctly_if_fields_blank():
    source_record = create_datacite_source_record_stub("<version />")
    assert Datacite.get_edition(source_record) is None


def test_get_edition_transforms_correctly_if_fields_missing():
    source_record = create_datacite_source_record_stub()
    assert Datacite.get_edition(source_record) is None


def test_get_file_formats_success():
    source_record = create_datacite_source_record_stub(
        """
        <formats>
         <format>application/vnd.openxmlformats-officedocument.spreadsheetml.sheet</format>
         <format>application/pdf</format>
         <format>application/pdf</format>
         <format>application/vnd.openxmlformats-officedocument.spreadsheetml.sheet</format>
         <format>application/pdf</format>
         <format>application/x-stata-syntax</format>
         <format>application/x-stata</format>
         <format>application/x-stata</format>
         <format>application/zip</format>
         <format>application/pdf</format>
         <format>application/pdf</format>
        </formats>
        """
    )
    assert Datacite.get_file_formats(source_record) == [
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
    ]


def test_get_file_formats_transforms_correctly_if_fields_blank():
    source_record = create_datacite_source_record_stub("<formats><format /></formats>")
    assert Datacite.get_file_formats(source_record) is None


def test_get_file_formats_transforms_correctly_if_fields_missing():
    source_record = create_datacite_source_record_stub()
    assert Datacite.get_file_formats(source_record) is None


def test_get_format_success():
    assert Datacite.get_format() == "electronic resource"


def test_get_funding_information_success():
    source_record = create_datacite_source_record_stub(
        """
        <fundingReferences>
         <fundingReference>
          <funderName>3ie, Nike Foundation</funderName>
          <funderIdentifier
          funderIdentifierType="Crossref FunderID">0987</funderIdentifier>
          <awardNumber awardURI="http://awards.example/7689">OW1/1012 (3ie)</awardNumber>
         </fundingReference>
        </fundingReferences>
        """
    )
    assert Datacite.get_funding_information(source_record) == [
        Funder(
            funder_name="3ie, Nike Foundation",
            funder_identifier="0987",
            funder_identifier_type="Crossref FunderID",
            award_number="OW1/1012 (3ie)",
            award_uri="http://awards.example/7689",
        )
    ]


def test_get_funding_information_transforms_correctly_if_fields_blank():
    source_record = create_datacite_source_record_stub(
        "<fundingReferences><fundingReference /></fundingReferences>"
    )
    assert Datacite.get_funding_information(source_record) is None


def test_get_funding_information_transforms_correctly_if_fields_missing():
    source_record = create_datacite_source_record_stub()
    assert Datacite.get_funding_information(source_record) is None


def test_get_identifiers_success():
    source_record = create_datacite_source_record_stub(
        """
        <identifier identifierType="DOI">10.7910/DVN/19PPE7</identifier>
        <alternateIdentifiers>
         <alternateIdentifier alternateIdentifierType="url">https://zenodo.org/record/5524465</alternateIdentifier>
        </alternateIdentifiers>
        <relatedIdentifiers>
         <relatedIdentifier relatedIdentifierType="DOI" relationType="IsCitedBy">
         10.1257/app.20150390</relatedIdentifier>
         <relatedIdentifier relationType="IsVersionOf">10.5281/zenodo.5524464
         </relatedIdentifier>
         <relatedIdentifier relatedIdentifierType="ISBN"
         relationType="IsIdenticalTo">1234567.5524464</relatedIdentifier>
         <relatedIdentifier relatedIdentifierType="ISBN" relationType="Other">
         1234567.5524464</relatedIdentifier>
         <relatedIdentifier relatedIdentifierType="URL" relationType="IsPartOf">
         https://zenodo.org/communities/astronomy-general</relatedIdentifier>
        </relatedIdentifiers>
        """
    )
    assert Datacite.get_identifiers(source_record) == [
        Identifier(value="10.7910/DVN/19PPE7", kind="DOI"),
        Identifier(value="https://zenodo.org/record/5524465", kind="url"),
        Identifier(value="1234567.5524464", kind="IsIdenticalTo"),
    ]


def test_get_identifiers_transforms_correctly_if_fields_blank():
    source_record = create_datacite_source_record_stub(
        """
        <identifier />
        <alternateIdentifiers>
         <alternateIdentifier />
        </alternateIdentifiers>
        <relatedIdentifiers>
         <relatedIdentifier />
        </relatedIdentifiers>
        """
    )
    assert Datacite.get_identifiers(source_record) is None


def test_get_identifiers_transforms_correctly_if_fields_missing():
    source_record = create_datacite_source_record_stub()
    assert Datacite.get_identifiers(source_record) is None


def test_get_languages_success():
    source_record = create_datacite_source_record_stub("<language>en_US</language>")
    assert Datacite.get_languages(source_record) == ["en_US"]


def test_get_languages_transforms_correctly_if_fields_blank():
    source_record = create_datacite_source_record_stub("<language />")
    assert Datacite.get_languages(source_record) is None


def test_get_languages_transforms_correctly_if_fields_missing():
    source_record = create_datacite_source_record_stub()
    assert Datacite.get_languages(source_record) is None


def test_get_links_success(datacite_record_all_fields):
    source_record = create_datacite_source_record_stub()
    datacite_transformer = Datacite("jpal", datacite_record_all_fields)
    assert datacite_transformer.get_links(source_record) == [
        Link(
            url="https://dataverse.harvard.edu/dataset.xhtml?persistentId=abc123",
            kind="Digital object URL",
            text="Digital object URL",
        )
    ]


def test_get_locations_success():
    source_record = create_datacite_source_record_stub(
        """
        <geoLocations>
         <geoLocation>
          <geoLocationPlace>A point on the globe</geoLocationPlace>
         </geoLocation>
        </geoLocations>
        """
    )
    assert Datacite.get_locations(source_record) == [
        Location(value="A point on the globe")
    ]


def test_get_locations_transforms_correctly_if_fields_blank():
    source_record = create_datacite_source_record_stub(
        "<geoLocations><geoLocation><geoLocationPlace /></geoLocation></geoLocations>"
    )
    assert Datacite.get_locations(source_record) is None


def test_get_locations_transforms_correctly_if_fields_missing():
    source_record = create_datacite_source_record_stub()
    assert Datacite.get_locations(source_record) is None


def test_get_notes_success():
    source_record = create_datacite_source_record_stub(
        """
        <resourceType resourceTypeGeneral="Dataset">Survey Data</resourceType>
        <descriptions>
         <description descriptionType="TechnicalInfo">Stata, 13</description>
        </descriptions>
        """
    )
    assert Datacite.get_notes(source_record) == [
        Note(value=["Survey Data"], kind="Datacite resource type"),
        Note(value=["Stata, 13"], kind="TechnicalInfo"),
    ]


def test_get_notes_transforms_correctly_if_fields_blank():
    source_record = create_datacite_source_record_stub(
        "<descriptions><description /></descriptions>"
    )
    assert Datacite.get_notes(source_record) is None


def test_get_notes_transforms_correctly_if_fields_missing():
    source_record = create_datacite_source_record_stub()
    assert Datacite.get_notes(source_record) is None


def test_get_publishers_success():
    source_record = create_datacite_source_record_stub(
        "<publisher>Harvard Dataverse</publisher>"
    )
    assert Datacite.get_publishers(source_record) == [Publisher(name="Harvard Dataverse")]


def test_get_publishers_transforms_correctly_if_fields_blank():
    source_record = create_datacite_source_record_stub("<publisher />")
    assert Datacite.get_publishers(source_record) is None


def test_get_publishers_transforms_correctly_if_fields_missing():
    source_record = create_datacite_source_record_stub()
    assert Datacite.get_publishers(source_record) is None


def test_get_related_items_success():
    metadata_insert = (
        '<relatedIdentifiers><relatedIdentifier relatedIdentifierType="DOI" '
        'relationType="IsCitedBy">10.1257/app.20150390</relatedIdentifier>'
        '<relatedIdentifier relationType="IsVersionOf">10.5281/zenodo.5524464'
        '</relatedIdentifier><relatedIdentifier relatedIdentifierType="ISBN" '
        'relationType="Other">1234567.5524464</relatedIdentifier><relatedIdentifier '
        'relatedIdentifierType="URL" relationType="IsPartOf">'
        "https://zenodo.org/communities/astronomy-general</relatedIdentifier>"
        "</relatedIdentifiers>"
    )
    source_record = create_datacite_source_record_stub(metadata_insert)
    assert Datacite.get_related_items(source_record) == [
        RelatedItem(relationship="IsCitedBy", uri="https://doi.org/10.1257/app.20150390"),
        RelatedItem(relationship="IsVersionOf", uri="10.5281/zenodo.5524464"),
        RelatedItem(relationship="Other", uri="1234567.5524464"),
        RelatedItem(
            relationship="IsPartOf",
            uri="https://zenodo.org/communities/astronomy-general",
        ),
    ]


def test_get_related_items_transforms_correctly_if_fields_blank():
    source_record = create_datacite_source_record_stub(
        "<relatedIdentifiers><relatedIdentifier /></relatedIdentifiers>"
    )
    assert Datacite.get_related_items(source_record) is None


def test_get_related_items_transforms_correctly_if_fields_missing():
    source_record = create_datacite_source_record_stub()
    assert Datacite.get_related_items(source_record) is None


def test_get_rights_success():
    source_record = create_datacite_source_record_stub(
        """
        <rightsList>
          <rights rightsURI="info:eu-repo/semantics/openAccess" />
          <rights
          rightsURI="http://creativecommons.org/publicdomain/zero/1.0">CC0 1.0</rights>
        </rightsList>
        """
    )
    assert Datacite.get_rights(source_record) == [
        Rights(description=None, kind=None, uri="info:eu-repo/semantics/openAccess"),
        Rights(
            description="CC0 1.0",
            kind=None,
            uri="http://creativecommons.org/publicdomain/zero/1.0",
        ),
    ]


def test_get_rights_transforms_correctly_if_fields_blank():
    source_record = create_datacite_source_record_stub(
        "<rightsList><rights /></rightsList>"
    )
    assert Datacite.get_rights(source_record) is None


def test_get_rights_transforms_correctly_if_fields_missing():
    source_record = create_datacite_source_record_stub()
    assert Datacite.get_rights(source_record) is None


def test_get_subjects_success():
    source_record = create_datacite_source_record_stub(
        """
        <subjects>
         <subject>Social Sciences</subject>
         <subject>Educational materials</subject>
         <subject subjectScheme="LCSH"
         >Adult education, education inputs, field experiments</subject>
         <subject subjectScheme="LCSH">Education</subject>
        </subjects>
        """
    )
    assert Datacite.get_subjects(source_record) == [
        Subject(
            value=["Social Sciences", "Educational materials"],
            kind="Subject scheme not provided",
        ),
        Subject(
            value=[
                "Adult education, education inputs, field experiments",
                "Education",
            ],
            kind="LCSH",
        ),
    ]


def test_get_subjects_transforms_correctly_if_fields_blank():
    source_record = create_datacite_source_record_stub("<subjects><subject /></subjects>")
    assert Datacite.get_subjects(source_record) is None


def test_get_subjects_transforms_correctly_if_fields_missing():
    source_record = create_datacite_source_record_stub()
    assert Datacite.get_subjects(source_record) is None


def test_get_summary_success():
    metadata_insert = (
        '<descriptions><description descriptionType="Abstract">Using a '
        "randomized field experiment in India, we evaluate the effectiveness of adult "
        "literacy and parental involvement interventions in improving children's "
        "learning. Households were assigned to receive either adult literacy (language "
        "and math) classes for mothers, training for mothers on how to enhance their "
        "children's learning at home, or a combination of the two programs. All three "
        "interventions had significant but modest impacts on childrens math scores. The "
        "interventions also increased mothers' test scores in both language and math, as "
        "well as a range of other outcomes reflecting greater involvement of mothers in "
        "their children's education.</description>"
    )
    source_record = create_datacite_source_record_stub(metadata_insert)
    assert Datacite.get_summary(source_record) == [
        "Using a randomized field experiment in India, we evaluate the effectiveness "
        "of adult literacy and parental involvement interventions in improving "
        "children's learning. Households were assigned to receive either adult "
        "literacy (language and math) classes for mothers, training for mothers on "
        "how to enhance their children's learning at home, or a combination of the "
        "two programs. All three interventions had significant but modest impacts on "
        "childrens math scores. The interventions also increased mothers' test scores"
        " in both language and math, as well as a range of other outcomes reflecting "
        "greater involvement of mothers in their children's education."
    ]


def test_get_summarty_transforms_correctly_if_fields_blank():
    source_record = create_datacite_source_record_stub(
        '<descriptions><description descriptionType="Abstract" /></descriptions>'
    )
    assert Datacite.get_summary(source_record) is None


def test_get_summary_transforms_correctly_if_fields_missing():
    source_record = create_datacite_source_record_stub()
    assert Datacite.get_summary(source_record) is None


def test_generate_name_identifier_url_orcid_scheme(datacite_record_all_fields):
    assert next(datacite_record_all_fields).contributors[0].identifier == [
        "https://orcid.org/0000-0000-0000-0000"
    ]


def test_generate_name_identifier_url_unknown_scheme(datacite_record_all_fields):
    assert next(datacite_record_all_fields).contributors[1].identifier == [
        "0000-0000-0000-0001"
    ]


def test_generate_name_identifier_url_no_identifier_scheme(
    datacite_record_all_fields,
):
    assert next(datacite_record_all_fields).contributors[2].identifier == [
        "0000-0000-0000-0002"
    ]


def test_generate_related_item_identifier_url_doi_type(datacite_record_all_fields):
    assert (
        next(datacite_record_all_fields).related_items[0].uri
        == "https://doi.org/10.1257/app.20150390"
    )


def test_generate_related_item_identifier_url_no_identifier_type(
    datacite_record_all_fields,
):
    assert (
        next(datacite_record_all_fields).related_items[1].uri == "10.5281/zenodo.5524464"
    )


def test_generate_related_item_identifier_url_unknown_type(
    datacite_record_all_fields,
):
    assert next(datacite_record_all_fields).related_items[2].uri == "1234567.5524464"


def test_generate_related_item_identifier_url_url_type(datacite_record_all_fields):
    assert (
        next(datacite_record_all_fields).related_items[3].uri
        == "https://zenodo.org/communities/astronomy-general"
    )
