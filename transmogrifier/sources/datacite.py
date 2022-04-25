from typing import Iterator

from bs4 import Tag

from transmogrifier.models import Contributor, Date, Identifier, Note, TimdexRecord


class Datacite:
    def __init__(
        self,
        source: str,
        source_base_url: str,
        source_name: str,
        input_records: Iterator[Tag],
    ) -> None:
        self.source = source
        self.source_base_url = source_base_url
        self.source_name = source_name
        self.input_records = input_records

    def __iter__(self) -> Iterator[TimdexRecord]:
        return self

    def __next__(self) -> TimdexRecord:
        xml = next(self.input_records)
        record = self.create_from_datacite_xml(
            self.source, self.source_base_url, self.source_name, xml
        )
        return record

    @classmethod
    def create_from_datacite_xml(
        cls, source: str, source_link_url: str, source_name: str, xml: Tag
    ) -> TimdexRecord:
        # Required fields in TIMDEX
        source_record_id = xml.header.find("identifier").string
        all_titles = xml.metadata.find_all("title")
        main_title = [t for t in all_titles if "titleType" not in t.attrs]
        if len(main_title) != 1:
            raise ValueError(
                "A record must have exactly one title. Titles found for record "
                f"{source_record_id}: {main_title}"
            )
        kwargs = {
            "source": source_name,
            "source_link": source_link_url + source_record_id,
            "timdex_record_id": f"{source}:{source_record_id.replace('/', '-')}",
            "title": main_title[0].string,
        }

        # Optional fields in TIMDEX, required in Datacite
        # content_type
        resource_type = xml.metadata.find("resourceType")
        if resource_type.string:
            kwargs["notes"] = [
                Note(value=[resource_type.string], kind="Datacite resource type")
            ]
        kwargs["content_type"] = [resource_type["resourceTypeGeneral"]]

        # contributors
        creators = xml.metadata.find_all("creator")
        for creator in creators:
            c = Contributor(
                value=creator.find("creatorName").string,
                affiliation=[a.string for a in creator.find_all("affiliation")] or None,
                identifier=[
                    cls.generate_name_identifier_url(name_identifier)
                    for name_identifier in creator.find_all("nameIdentifier")
                ]
                or None,
                kind="Creator",
            )
            kwargs.setdefault("contributors", []).append(c)

        contributors = xml.metadata.find_all("contributor")
        for contributor in contributors:
            c = Contributor(
                value=contributor.find("contributorName").string,
                affiliation=[a.string for a in contributor.find_all("affiliation")]
                or None,
                identifier=[
                    cls.generate_name_identifier_url(name_identifier)
                    for name_identifier in contributor.find_all("nameIdentifier")
                ]
                or None,
                kind=contributor["contributorType"],
            )
            kwargs.setdefault("contributors", []).append(c)

        # dates
        publication_year = xml.metadata.find("publicationYear").string
        kwargs["dates"] = [Date(kind="Publication date", value=publication_year)]

        # identifiers
        identifier_xml = xml.metadata.find("identifier")
        kwargs["identifiers"] = [
            Identifier(
                value=identifier_xml.string,
                kind=identifier_xml["identifierType"],
            ),
        ]

        # publication_information
        kwargs["publication_information"] = [xml.metadata.find("publisher").string]

        return TimdexRecord(**kwargs)

    @classmethod
    def generate_name_identifier_url(cls, name_identifier):
        if name_identifier["nameIdentifierScheme"] == "ORCID":
            base_url = "https://orcid.org/"
        else:
            base_url = ""
        return base_url + name_identifier.string
