import logging
from typing import Iterator

from bs4 import Tag

from transmogrifier.models import (
    AlternateTitle,
    Contributor,
    Date,
    Funder,
    Identifier,
    Location,
    Note,
    RelatedItem,
    Rights,
    Subject,
    TimdexRecord,
)

logger = logging.getLogger(__name__)


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
        """
        Args:
            source: A label for the source repository that is prepended to the
            timdex_record_id.
            source_link_url: A direct link to the source metadata record.
            source_name: The full human-readable name of the source repository to be
            used in the TIMDEX record.
            xml: A BeautifulSoup Tag representing a single Datacite record in
            oai_datacite XML.
        """
        # Required fields in TIMDEX
        source_record_id = xml.header.find("identifier").string
        kwargs = {
            "source": source_name,
            "source_link": source_link_url + source_record_id,
            "timdex_record_id": f"{source}:{source_record_id.replace('/', '-')}",
            "format": "electronic resource",
        }
        # main title
        all_titles = xml.metadata.find_all("title")
        main_title = [t for t in all_titles if "titleType" not in t.attrs]
        if len(main_title) != 1:
            raise ValueError(
                "A record must have exactly one title. Titles found for record "
                f"{source_record_id}: {main_title}"
            )
        subtitles = [
            s
            for s in all_titles
            if "titleType" in s.attrs and s.attrs["titleType"] == "Subtitle"
        ]
        concat_subtitles = ""
        for subtitle in subtitles:
            concat_subtitles += " " + subtitle.string
        if concat_subtitles:
            kwargs["title"] = f"{main_title[0].string}:{concat_subtitles}"
        else:
            kwargs["title"] = main_title[0].string

        # Optional fields in TIMDEX, required in Datacite
        # alternate_titles, uses full title list retrieved for main title field
        alternate_titles = [
            t
            for t in all_titles
            if "titleType" in t.attrs and t.attrs["titleType"] == "AlternativeTitle"
        ]
        for alternate_title in alternate_titles:
            a = AlternateTitle(
                value=alternate_title.string,
                kind="alternative",
            )
            kwargs.setdefault("alternate_titles", []).append(a)

        # content_type
        resource_type = xml.metadata.find("resourceType")
        if resource_type is None:
            logger.warning(
                "Datacite record %s missing required Datacite field resourceType",
                source_record_id,
            )
        else:
            if resource_type.string:
                kwargs["notes"] = [
                    Note(value=resource_type.string, kind="Datacite resource type")
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
        publication_year = xml.metadata.find("publicationYear")
        if publication_year is None:
            logger.warning(
                "Datacite record %s missing required Datacite field publicationYear",
                source_record_id,
            )
        else:
            kwargs["dates"] = [
                Date(kind="Publication date", value=publication_year.string)
            ]
        dates = xml.metadata.find_all("date")
        for date in dates:
            d = Date(value=date.string)
            if "dateType" in date.attrs:
                d.kind = date.attrs["dateType"]
            if "dateInformation" in date.attrs:
                d.note = date.attrs["dateInformation"]
            kwargs.setdefault("dates", []).append(d)

        # edition
        edition = xml.metadata.find("version")
        if edition:
            kwargs["edition"] = edition.string

        # file_formats
        file_formats = xml.metadata.find_all("format")
        for file_format in file_formats:
            kwargs.setdefault("file_formats", []).append(file_format.string)

        # funding_information
        funding_references = xml.metadata.find_all("fundingReference")
        for funding_reference in funding_references:
            f = Funder(
                funder_name=funding_reference.find("funderName").string,
            )
            if funding_reference.find("funderIdentifier"):
                funder_identifier = funding_reference.find("funderIdentifier")
                f.funder_identifier = funder_identifier.string
                if "funderIdentifierType" in funder_identifier.attrs:
                    f_id_type = funder_identifier.attrs["funderIdentifierType"]
                    f.funder_identifier_type = f_id_type
            if funding_reference.find("awardNumber"):
                award_number = funding_reference.find("awardNumber")
                f.award_number = award_number.string
                if "awardURI" in award_number.attrs:
                    f.award_uri = award_number.attrs["awardURI"]
            kwargs.setdefault("funding_information", []).append(f)

        # identifiers
        identifier_xml = xml.metadata.find("identifier")
        kwargs["identifiers"] = [
            Identifier(
                value=identifier_xml.string,
                kind=identifier_xml["identifierType"],
            ),
        ]
        # language
        language = xml.metadata.find("language")
        if language:
            kwargs["languages"] = [language.string]

        # locations
        locations = xml.metadata.find_all("geoLocationPlace")
        for location in locations:
            kwargs.setdefault("locations", []).append(Location(value=location.string))

        # notes
        descriptions = xml.metadata.find_all("description")
        for description in [
            d
            for d in descriptions
            if "descriptionType" in d.attrs and d.attrs["descriptionType"] != "Abstract"
        ]:
            n = Note(
                value=description.string, kind=description.attrs["descriptionType"]
            )
            kwargs.setdefault("notes", []).append(n)

        # publication_information
        publisher = xml.metadata.find("publisher")
        if publisher is None:
            logger.warning(
                "Datacite record %s missing required Datacite field publisher",
                source_record_id,
            )
        else:
            kwargs["publication_information"] = [publisher.string]

        # related_items
        related_items = xml.metadata.find_all("relatedIdentifier")
        for related_item in related_items:
            ri = RelatedItem(uri=related_item.string)
            if "relationType" in related_item.attrs:
                ri.kind = related_item.attrs["relationType"]
            kwargs.setdefault("related_items", []).append(ri)

        # rights
        rights_list = xml.metadata.find_all("rights")
        for rights in rights_list:
            r = Rights()
            if rights.string:
                r.description = rights.string
            if "rightsURI" in rights.attrs:
                r.uri = rights.attrs["rightsURI"]
            kwargs.setdefault("rights", []).append(r)

        # subjects
        subjects = xml.metadata.find_all("subject")
        for subject in subjects:
            s = Subject(value=subject.string)
            if "subjectScheme" in subject.attrs:
                s.kind = subject.attrs["subjectScheme"]
            kwargs.setdefault("subjects", []).append(s)

        # summary, uses description list retrieved for notes field
        for description in [
            d
            for d in descriptions
            if "descriptionType" in d.attrs and d.attrs["descriptionType"] == "Abstract"
        ]:
            kwargs.setdefault("summary", []).append(description.string)

        return TimdexRecord(**kwargs)

    @classmethod
    def generate_name_identifier_url(cls, name_identifier):
        """
        Generate a full name identifier URL with the specified scheme.
        Args:
            name_identifier: An BeautifulSoup Tag Tag representing a Datacite
            nameIdentifier XML field.
        """
        if name_identifier["nameIdentifierScheme"] == "ORCID":
            base_url = "https://orcid.org/"
        else:
            base_url = ""
        return base_url + name_identifier.string
