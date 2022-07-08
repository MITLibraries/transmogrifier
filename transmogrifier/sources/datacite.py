import logging
from typing import Dict, List

from bs4 import Tag

import transmogrifier.models as timdex
from transmogrifier.helpers import generate_citation
from transmogrifier.sources.transformer import Transformer

logger = logging.getLogger(__name__)


class Datacite(Transformer):
    """Datacite transformer."""

    def transform(self, xml: Tag) -> timdex.TimdexRecord:
        """
        Transform a Datacite XML record to a TIMDEX record.

        Overrides the base Transformer.transform() method.

        Args:
            xml: A BeautifulSoup Tag representing a single Datacite XML record.
        """

        # Required fields in TIMDEX
        source_record_id = self.create_source_record_id(xml)
        all_titles = xml.metadata.find_all("title")
        main_title = [t for t in all_titles if "titleType" not in t.attrs]
        if len(main_title) != 1:
            raise ValueError(
                "A record must have exactly one title. Titles found for record "
                f"{source_record_id}: {main_title}"
            )
        if not main_title[0].string:
            raise ValueError(
                f"Title field cannot be empty, record {source_record_id} had title "
                f"field value of '{main_title[0]}'"
            )
        kwargs = {
            "source": self.source_name,
            "source_link": self.source_base_url + source_record_id,
            "timdex_record_id": f"{self.source}:{source_record_id.replace('/', '-')}",
            "title": main_title[0].string,
        }

        # Optional fields in TIMDEX
        # alternate_titles, uses full title list retrieved for main title field
        for alternate_title in [
            t for t in all_titles if "titleType" in t.attrs and t.string
        ]:
            kwargs.setdefault("alternate_titles", []).append(
                timdex.AlternateTitle(
                    value=alternate_title.string,
                    kind=alternate_title["titleType"],
                )
            )

        # content_type
        resource_type = xml.metadata.find("resourceType")
        if resource_type and resource_type.string:
            kwargs["notes"] = [
                timdex.Note(value=[resource_type.string], kind="Datacite resource type")
            ]
            if resource_type["resourceTypeGeneral"]:
                kwargs["content_type"] = [resource_type["resourceTypeGeneral"]]
        else:
            logger.warning(
                "Datacite record %s missing required Datacite field resourceType",
                source_record_id,
            )

        # contributors
        for creator in xml.metadata.find_all("creator"):
            creator_name_element = creator.find("creatorName")
            if creator_name_element and creator_name_element.string:
                kwargs.setdefault("contributors", []).append(
                    timdex.Contributor(
                        value=creator_name_element.string,
                        affiliation=[a.string for a in creator.find_all("affiliation")]
                        or None,
                        identifier=[
                            self.generate_name_identifier_url(name_identifier)
                            for name_identifier in creator.find_all("nameIdentifier")
                        ]
                        or None,
                        kind="Creator",
                    )
                )

        for contributor in xml.metadata.find_all("contributor"):
            contributor_name_element = contributor.find("contributorName")
            if contributor_name_element and contributor_name_element.string:
                kwargs.setdefault("contributors", []).append(
                    timdex.Contributor(
                        value=contributor_name_element.string,
                        affiliation=[
                            a.string for a in contributor.find_all("affiliation")
                        ]
                        or None,
                        identifier=[
                            self.generate_name_identifier_url(name_identifier)
                            for name_identifier in contributor.find_all(
                                "nameIdentifier"
                            )
                        ]
                        or None,
                        kind=contributor["contributorType"],
                    )
                )

        # dates
        publication_year = xml.metadata.find("publicationYear")
        if not publication_year or not publication_year.string:
            logger.warning(
                "Datacite record %s missing required Datacite field publicationYear",
                source_record_id,
            )
        else:
            kwargs["dates"] = [
                timdex.Date(kind="Publication date", value=publication_year.string)
            ]

        for date in [d for d in xml.metadata.find_all("date") if d.string]:
            if "/" in date.string:
                d = timdex.Date(
                    range=timdex.Date_Range(
                        gte=date.string[: date.string.index("/")],
                        lte=date.string[date.string.index("/") + 1 :],
                    )
                )
            else:
                d = timdex.Date(value=date.string)
            d.note = date.get("dateInformation")
            d.kind = date.get("dateType")
            kwargs.setdefault("dates", []).append(d)

        # edition
        edition = xml.metadata.find("version")
        if edition and edition.string:
            kwargs["edition"] = edition.string

        # file_formats
        kwargs["file_formats"] = [
            f.string for f in xml.metadata.find_all("format") if f.string
        ] or None

        # format
        kwargs["format"] = "electronic resource"

        # funding_information
        for funding_reference in [
            fr for fr in xml.metadata.find_all("fundingReference")
        ]:
            f = timdex.Funder()
            funder_name = funding_reference.find("funderName")
            if funder_name.string:
                f.funder_name = funder_name.string
            award_number = funding_reference.find("awardNumber")
            if award_number and award_number.string:
                f.award_number = award_number.string
                f.award_uri = award_number.get("awardURI")
            funder_identifier = funding_reference.find("funderIdentifier")
            if funder_identifier and funder_identifier.string:
                f.funder_identifier = funder_identifier.string
                f.funder_identifier_type = funder_identifier.get("funderIdentifierType")
            if f != timdex.Funder():
                kwargs.setdefault("funding_information", []).append(f)

        # identifiers
        identifier_xml = xml.metadata.find("identifier")
        kwargs["identifiers"] = [
            timdex.Identifier(
                value=identifier_xml.string,
                kind=identifier_xml.get(
                    "identifierType", "Identifier kind not specified"
                ),
            ),
        ]
        for alternate_identifier in [
            i for i in xml.metadata.find_all("alternateIdentifier") if i.string
        ]:
            kwargs["identifiers"].append(
                timdex.Identifier(
                    value=alternate_identifier.string,
                    kind=alternate_identifier.get(
                        "alternateIdentifierType", "Identifier kind not specified"
                    ),
                )
            )

        related_identifiers = xml.metadata.find_all("relatedIdentifier")
        for related_identifier in [
            i
            for i in related_identifiers
            if i.get("relationType") == "IsIdenticalTo" and i.string
        ]:
            i = timdex.Identifier(
                value=self.generate_related_item_identifier_url(related_identifier),
                kind=related_identifier.get(
                    "relationType", "Identifier kind not specified"
                ),
            )
            kwargs["identifiers"].append(i)

        # language
        language = xml.metadata.find("language")
        if language and language.string:
            kwargs["languages"] = [language.string]

        # links
        kwargs["links"] = [
            timdex.Link(
                kind="Digital object URL",
                text="Digital object URL",
                url=kwargs["source_link"],
            )
        ]

        # locations
        for location in [
            gl for gl in xml.metadata.find_all("geoLocationPlace") if gl.string
        ]:
            kwargs.setdefault("locations", []).append(
                timdex.Location(value=location.string)
            )

        # notes
        descriptions = xml.metadata.find_all("description")
        for description in [d for d in descriptions if d.string]:
            if "descriptionType" not in description.attrs:
                logger.warning(
                    "Datacite record %s missing required Datacite attribute "
                    "@descriptionType",
                    source_record_id,
                )
            if description.get("descriptionType") != "Abstract":
                kwargs.setdefault("notes", []).append(
                    timdex.Note(
                        value=[description.string],
                        kind=description.get("descriptionType"),
                    )
                )

        # publication_information
        publisher = xml.metadata.find("publisher")
        if not publication_year or not publication_year.string:
            logger.warning(
                "Datacite record %s missing required Datacite field publisher",
                source_record_id,
            )
        else:
            kwargs["publication_information"] = [publisher.string]

        # related_items, uses related_identifiers retrieved for identifiers
        for related_identifier in [i for i in related_identifiers if i.string]:
            kwargs.setdefault("related_items", []).append(
                timdex.RelatedItem(
                    uri=self.generate_related_item_identifier_url(related_identifier),
                    relationship=related_identifier.get("relationType"),
                )
            )

        # rights
        for right in [
            r for r in xml.metadata.find_all("rights") if r.string or r.get("rightsURI")
        ]:
            kwargs.setdefault("rights", []).append(
                timdex.Rights(
                    description=right.string or None, uri=right.get("rightsURI")
                )
            )

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
        kwargs["subjects"] = [
            timdex.Subject(value=value, kind=key)
            for key, value in subjects_dict.items()
        ] or None

        # summary, uses description list retrieved for notes field
        kwargs["summary"] = [
            d.string
            for d in descriptions
            if d.get("descriptionType") == "Abstract" and d.string
        ] or None

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
