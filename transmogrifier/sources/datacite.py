import logging
from typing import Dict, List, Optional

from bs4 import Tag

import transmogrifier.models as timdex
from transmogrifier.sources.transformer import Transformer

logger = logging.getLogger(__name__)


class Datacite(Transformer):
    """Datacite transformer."""

    def get_optional_fields(self, xml: Tag) -> Optional[dict]:
        """
        Retrieve optional TIMDEX fields from a Datacite XML record.

        Overrides metaclass get_optional_fields() method.

        Args:
            xml: A BeautifulSoup Tag representing a single Datacite record in
                oai_datacite XML.
        """
        fields: dict = {}
        source_record_id = self.get_source_record_id(xml)

        # alternate_titles
        for alternate_title in [
            t for t in xml.find_all("title") if "titleType" in t.attrs and t.string
        ]:
            fields.setdefault("alternate_titles", []).append(
                timdex.AlternateTitle(
                    value=alternate_title.string,
                    kind=alternate_title["titleType"],
                )
            )

        # content_type
        resource_type = xml.metadata.find("resourceType")
        if resource_type:
            if resource_type.string:
                fields["notes"] = [
                    timdex.Note(
                        value=[resource_type.string], kind="Datacite resource type"
                    )
                ]
            if content_type_list := resource_type.get("resourceTypeGeneral"):
                if self.valid_content_types([content_type_list]):
                    fields["content_type"] = [content_type_list]
                else:
                    return None
        else:
            logger.warning(
                "Datacite record %s missing required Datacite field resourceType",
                source_record_id,
            )

        # contributors
        for creator in xml.metadata.find_all("creator"):
            creator_name_element = creator.find("creatorName")
            if creator_name_element and creator_name_element.string:
                fields.setdefault("contributors", []).append(
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
                fields.setdefault("contributors", []).append(
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
            fields["dates"] = [
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
            fields.setdefault("dates", []).append(d)

        # edition
        edition = xml.metadata.find("version")
        if edition and edition.string:
            fields["edition"] = edition.string

        # file_formats
        fields["file_formats"] = [
            f.string for f in xml.metadata.find_all("format") if f.string
        ] or None

        # format
        fields["format"] = "electronic resource"

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
                fields.setdefault("funding_information", []).append(f)

        # identifiers
        identifier_xml = xml.metadata.find("identifier")
        fields["identifiers"] = [
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
            fields["identifiers"].append(
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
            fields["identifiers"].append(i)

        # language
        language = xml.metadata.find("language")
        if language and language.string:
            fields["languages"] = [language.string]

        # links
        fields["links"] = [
            timdex.Link(
                kind="Digital object URL",
                text="Digital object URL",
                url=self.source_base_url + source_record_id,
            )
        ]

        # locations
        for location in [
            gl for gl in xml.metadata.find_all("geoLocationPlace") if gl.string
        ]:
            fields.setdefault("locations", []).append(
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
                fields.setdefault("notes", []).append(
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
            fields["publication_information"] = [publisher.string]

        # related_items, uses related_identifiers retrieved for identifiers
        for related_identifier in [i for i in related_identifiers if i.string]:
            fields.setdefault("related_items", []).append(
                timdex.RelatedItem(
                    uri=self.generate_related_item_identifier_url(related_identifier),
                    relationship=related_identifier.get("relationType"),
                )
            )

        # rights
        for right in [
            r for r in xml.metadata.find_all("rights") if r.string or r.get("rightsURI")
        ]:
            fields.setdefault("rights", []).append(
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
        fields["subjects"] = [
            timdex.Subject(value=value, kind=key)
            for key, value in subjects_dict.items()
        ] or None

        # summary, uses description list retrieved for notes field
        fields["summary"] = [
            d.string
            for d in descriptions
            if d.get("descriptionType") == "Abstract" and d.string
        ] or None

        return fields

    @classmethod
    def get_main_titles(cls, xml: Tag) -> list[str]:
        """
        Retrieve main title(s) from a Datacite XML record.

        Overrides metaclass get_main_titles() method.

        Args:
            xml: A BeautifulSoup Tag representing a single Datacite record in
                oai_datacite XML.
        """
        return [t for t in xml.metadata.find_all("title", titleType=False)]

    @classmethod
    def get_source_record_id(cls, xml: Tag) -> str:
        """
        Get the source record ID from a Datacite XML record.

        Overrides metaclass get_source_record_id() method.

        Args:
            xml: A BeautifulSoup Tag representing a single Datacite record in
                oai_datacite XML.
        """
        return xml.header.find("identifier").string

    @classmethod
    def generate_name_identifier_url(cls, name_identifier: Tag) -> str:
        """
        Generate a full name identifier URL with the specified scheme.
        Args:
            name_identifier: A BeautifulSoup Tag representing a Datacite
                nameIdentifier XML field.
        """
        if name_identifier.get("nameIdentifierScheme") == "ORCID":
            base_url = "https://orcid.org/"
        else:
            base_url = ""
        return base_url + name_identifier.string

    @classmethod
    def generate_related_item_identifier_url(cls, related_item_identifier: Tag) -> str:
        """
        Generate a full related item identifier URL with the specified scheme.
        Args:
            related_item_identifier: A BeautifulSoup Tag representing a Datacite
                relatedIdentifier XML field.
        """
        if related_item_identifier.get("relatedIdentifierType") == "DOI":
            base_url = "https://doi.org/"
        elif related_item_identifier.get("relatedIdentifierType") == "URL":
            base_url = ""
        else:
            base_url = ""
        return base_url + related_item_identifier.string

    @classmethod
    def valid_content_types(cls, content_type_list: List[str]) -> bool:
        """
        Validate a list content_type values from a Datacite XML record.

        May be overridden by source subclasses that require content type validation.

        Args:
            content_type_list: A list of content_type values.
        """
        return True
