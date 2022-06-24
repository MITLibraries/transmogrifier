import logging
from typing import Dict, Iterator, List

from bs4 import Tag

import transmogrifier.models as timdex
from transmogrifier.helpers import generate_citation

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

    def __iter__(self) -> Iterator[timdex.TimdexRecord]:
        return self

    def __next__(self) -> timdex.TimdexRecord:
        xml = next(self.input_records)
        record = self.create_from_datacite_xml(
            self.source, self.source_base_url, self.source_name, xml
        )
        return record

    @classmethod
    def create_from_datacite_xml(
        cls, source: str, source_base_url: str, source_name: str, xml: Tag
    ) -> timdex.TimdexRecord:
        """
        Args:
            source: A label for the source repository that is prepended to the
            timdex_record_id.
            source_base_url: The base URL for the source system from which direct links
            to source metadata records can be constructed.
            source_name: The full human-readable name of the source repository to be
            used in the TIMDEX record.
            xml: A BeautifulSoup Tag representing a single Datacite record in
            oai_datacite XML.
        """
        # Required fields in TIMDEX
        source_record_id = cls.create_source_record_id(xml)
        all_titles = xml.metadata.find_all("title")
        main_title = [t for t in all_titles if "titleType" not in t.attrs]
        if len(main_title) != 1:
            raise ValueError(
                "A record must have exactly one title. Titles found for record "
                f"{source_record_id}: {main_title}"
            )
        kwargs = {
            "source": source_name,
            "source_link": source_base_url + source_record_id,
            "timdex_record_id": f"{source}:{source_record_id.replace('/', '-')}",
            "title": main_title[0].string,
        }

        # Optional fields in TIMDEX
        # alternate_titles, uses full title list retrieved for main title field
        alternate_titles = [t for t in all_titles if "titleType" in t.attrs]
        for alternate_title in alternate_titles:
            a = timdex.AlternateTitle(
                value=alternate_title.string,
                kind=alternate_title.attrs["titleType"],
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
                    timdex.Note(
                        value=[resource_type.string], kind="Datacite resource type"
                    )
                ]
            kwargs["content_type"] = [resource_type["resourceTypeGeneral"]]

        # contributors
        creators = xml.metadata.find_all("creator")
        for creator in creators:
            c = timdex.Contributor(
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
            contributor_name = contributor.find("contributorName").string
            c = timdex.Contributor(
                value=contributor_name,
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
                timdex.Date(kind="Publication date", value=publication_year.string)
            ]
        dates = xml.metadata.find_all("date")
        for date in dates:
            if "/" in date.string:
                d = timdex.Date(
                    range=timdex.Date_Range(
                        gte=date.string[: date.string.index("/")],
                        lte=date.string[date.string.index("/") + 1 :],
                    )
                )
            else:
                d = timdex.Date(value=date.string)
            if "dateInformation" in date.attrs:
                d.note = date.attrs["dateInformation"]
            if "dateType" in date.attrs:
                d.kind = date.attrs["dateType"]
            kwargs.setdefault("dates", []).append(d)

        # edition
        edition = xml.metadata.find("version")
        if edition:
            kwargs["edition"] = edition.string

        # file_formats
        file_formats = xml.metadata.find_all("format")
        for file_format in file_formats:
            kwargs.setdefault("file_formats", []).append(file_format.string)

        # format
        kwargs["format"] = "electronic resource"

        # funding_information
        funding_references = xml.metadata.find_all("fundingReference")
        for funding_reference in funding_references:
            f = timdex.Funder(
                funder_name=funding_reference.find("funderName").string,
            )
            award_number = funding_reference.find("awardNumber")
            if award_number:
                f.award_number = award_number.string
                if "awardURI" in award_number.attrs:
                    f.award_uri = award_number.attrs["awardURI"]
            funder_identifier = funding_reference.find("funderIdentifier")
            if funder_identifier:
                f.funder_identifier = funder_identifier.string
                if "funderIdentifierType" in funder_identifier.attrs:
                    f_id_type = funder_identifier.attrs["funderIdentifierType"]
                    f.funder_identifier_type = f_id_type
            kwargs.setdefault("funding_information", []).append(f)

        # identifiers
        identifier_xml = xml.metadata.find("identifier")
        kwargs["identifiers"] = [
            timdex.Identifier(
                value=identifier_xml.string,
                kind=identifier_xml["identifierType"],
            ),
        ]
        alternate_identifiers = xml.metadata.find_all("alternateIdentifier")
        for alternate_identifier in alternate_identifiers:
            i = timdex.Identifier(
                value=alternate_identifier.string,
            )
            if "alternateIdentifierType" in alternate_identifier.attrs:
                i.kind = alternate_identifier.attrs["alternateIdentifierType"]
            kwargs["identifiers"].append(i)

        related_identifiers = xml.metadata.find_all("relatedIdentifier")
        for related_identifier in [
            i
            for i in related_identifiers
            if "relationType" in i.attrs and i.attrs["relationType"] == "IsIdenticalTo"
        ]:
            i = timdex.Identifier(
                value=cls.generate_related_item_identifier_url(related_identifier),
                kind=related_identifier.attrs["relationType"],
            )
            kwargs["identifiers"].append(i)

        # language
        language = xml.metadata.find("language")
        if language:
            kwargs["languages"] = [language.string]

        # locations
        locations = xml.metadata.find_all("geoLocationPlace")
        for location in locations:
            kwargs.setdefault("locations", []).append(
                timdex.Location(value=location.string)
            )

        # notes
        descriptions = xml.metadata.find_all("description")
        for description in descriptions:
            if "descriptionType" not in description.attrs:
                logger.warning(
                    "Datacite record %s missing required Datacite attribute "
                    "@descriptionType",
                    source_record_id,
                )
            else:
                if description.attrs["descriptionType"] != "Abstract":
                    n = timdex.Note(
                        value=[description.string],
                        kind=description.attrs["descriptionType"],
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

        # related_items, uses related_identifiers retrieved for identifiers
        for related_identifier in related_identifiers:
            ri = timdex.RelatedItem(
                uri=cls.generate_related_item_identifier_url(related_identifier)
            )
            if "relationType" in related_identifier.attrs:
                ri.relationship = related_identifier.attrs["relationType"]
            kwargs.setdefault("related_items", []).append(ri)

        # rights
        rights_list = xml.metadata.find_all("rights")
        for rights in rights_list:
            r = timdex.Rights()
            if rights.string:
                r.description = rights.string
            if "rightsURI" in rights.attrs:
                r.uri = rights.attrs["rightsURI"]
            kwargs.setdefault("rights", []).append(r)

        # subjects
        subjects_dict: Dict[str, List[str]] = {}
        for subject in [s for s in xml.metadata.find_all("subject") if s.string]:
            if subject.get("subjectScheme") is None:
                subjects_dict.setdefault("Subject scheme not provided", []).append(
                    subject.string
                )
            else:
                subjects_dict.setdefault(subject.attrs["subjectScheme"], []).append(
                    subject.string
                )
        for key, value in subjects_dict.items():
            kwargs.setdefault("subjects", []).append(
                timdex.Subject(value=value, kind=key)
            )

        # summary, uses description list retrieved for notes field
        for description in [
            d
            for d in descriptions
            if "descriptionType" in d.attrs and d.attrs["descriptionType"] == "Abstract"
        ]:
            kwargs.setdefault("summary", []).append(description.string)

        # citation, generate citation from other fields
        kwargs["citation"] = generate_citation(kwargs)

        return timdex.TimdexRecord(**kwargs)

    @classmethod
    def create_source_record_id(cls, xml: Tag) -> str:
        """
        Create a source record ID from a Datacite XML record.
        Args:
            xml: A BeautifulSoup Tag representing a single Datacite record in
            oai_datacite XML.
        """
        source_record_id = xml.header.find("identifier").string
        return source_record_id

    @classmethod
    def generate_name_identifier_url(cls, name_identifier):
        """
        Generate a full name identifier URL with the specified scheme.
        Args:
            name_identifier: An BeautifulSoup Tag Tag representing a Datacite
            nameIdentifier XML field.
        """
        if name_identifier.get("nameIdentifierScheme") == "ORCID":
            base_url = "https://orcid.org/"
        else:
            base_url = ""
        return base_url + name_identifier.string

    @classmethod
    def generate_related_item_identifier_url(cls, related_item_identifier):
        """
        Generate a full related item identifier URL with the specified scheme.
        Args:
            related_item_identifier: An BeautifulSoup Tag Tag representing a Datacite
            relatedIdentifier XML field.
        """
        if related_item_identifier.get("relatedIdentifierType") == "DOI":
            base_url = "https://doi.org/"
        elif related_item_identifier.get("relatedIdentifierType") == "URL":
            base_url = ""
        else:
            base_url = ""
        return base_url + related_item_identifier.string
