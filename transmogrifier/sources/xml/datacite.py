import logging
from collections.abc import Iterator

from bs4 import Tag  # type: ignore[import-untyped]

import transmogrifier.models as timdex
from transmogrifier.exceptions import SkippedRecordEvent
from transmogrifier.helpers import validate_date, validate_date_range
from transmogrifier.sources.xmltransformer import XMLTransformer

logger = logging.getLogger(__name__)


class Datacite(XMLTransformer):
    """Datacite transformer."""

    def get_optional_fields(self, source_record: Tag) -> dict | None:
        """
        Retrieve optional TIMDEX fields from a Datacite XML record.

        Overrides metaclass get_optional_fields() method.

        Args:
            source_record: A BeautifulSoup Tag representing a single Datacite record in
                oai_datacite XML.
        """
        fields: dict = {}
        source_record_id = self.get_source_record_id(source_record)

        # alternate_titles
        fields["alternate_titles"] = self.get_alternate_titles(source_record)

        # content_type
        fields["content_type"] = self.get_content_type(source_record, source_record_id)

        # contributors
        fields["contributors"] = self.get_contributors(source_record)

        # dates
        if publication_year := source_record.metadata.find(
            "publicationYear", string=True
        ):
            publication_year = str(publication_year.string.strip())
            if validate_date(
                publication_year,
                source_record_id,
            ):
                fields["dates"] = [
                    timdex.Date(kind="Publication date", value=publication_year)
                ]
        else:
            logger.warning(
                "Datacite record %s missing required Datacite field publicationYear",
                source_record_id,
            )

        for date in source_record.metadata.find_all("date"):
            d = timdex.Date()
            if date_value := date.string:
                date_value = str(date_value)
                if "/" in date_value:
                    split = date_value.index("/")
                    gte_date = date_value[:split].strip()
                    lte_date = date_value[split + 1 :].strip()
                    if validate_date_range(
                        gte_date,
                        lte_date,
                        source_record_id,
                    ):
                        d.range = timdex.DateRange(
                            gte=gte_date,
                            lte=lte_date,
                        )
                else:
                    d.value = (
                        date_value.strip()
                        if validate_date(
                            date_value,
                            source_record_id,
                        )
                        else None
                    )
            d.note = date.get("dateInformation") or None
            if any([d.note, d.range, d.value]):
                d.kind = date.get("dateType") or None
                fields.setdefault("dates", []).append(d)

        # edition
        if edition := source_record.metadata.find("version", string=True):
            fields["edition"] = edition.string

        # file_formats
        fields["file_formats"] = [
            f.string for f in source_record.metadata.find_all("format", string=True)
        ] or None

        # format
        fields["format"] = "electronic resource"

        # funding_information
        for funding_reference in source_record.metadata.find_all("fundingReference"):
            f = timdex.Funder()
            if funder_name := funding_reference.find("funderName", string=True):
                f.funder_name = funder_name.string
            if award_number := funding_reference.find("awardNumber"):
                f.award_number = award_number.string or None
                f.award_uri = award_number.get("awardURI") or None
            if funder_identifier := funding_reference.find(
                "funderIdentifier", string=True
            ):
                f.funder_identifier = funder_identifier.string
                f.funder_identifier_type = (
                    funder_identifier.get("funderIdentifierType") or None
                )
            if f != timdex.Funder():
                fields.setdefault("funding_information", []).append(f)

        # identifiers
        if identifier_xml := source_record.metadata.find("identifier", string=True):
            fields.setdefault("identifiers", []).append(
                timdex.Identifier(
                    value=identifier_xml.string,
                    kind=identifier_xml.get("identifierType") or "Not specified",
                )
            )
        for alternate_identifier in source_record.metadata.find_all(
            "alternateIdentifier", string=True
        ):
            fields.setdefault("identifiers", []).append(
                timdex.Identifier(
                    value=alternate_identifier.string,
                    kind=alternate_identifier.get("alternateIdentifierType")
                    or "Not specified",
                )
            )

        related_identifiers = source_record.metadata.find_all(
            "relatedIdentifier", string=True
        )
        for related_identifier in [
            ri for ri in related_identifiers if ri.get("relationType") == "IsIdenticalTo"
        ]:
            fields.setdefault("identifiers", []).append(
                timdex.Identifier(
                    value=self.generate_related_item_identifier_url(related_identifier),
                    kind=related_identifier["relationType"],
                )
            )

        # language
        if language := source_record.metadata.find("language", string=True):
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
        for location in source_record.metadata.find_all("geoLocationPlace", string=True):
            fields.setdefault("locations", []).append(
                timdex.Location(value=location.string)
            )

        # notes
        if resource_type := source_record.metadata.find("resourceType", string=True):
            fields.setdefault("notes", []).append(
                timdex.Note(
                    value=[str(resource_type.string)],
                    kind="Datacite resource type",
                )
            )
        descriptions = source_record.metadata.find_all("description", string=True)
        for description in descriptions:
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
                        kind=description.get("descriptionType") or None,
                    )
                )

        # publishers
        if publisher := source_record.metadata.find("publisher", string=True):
            fields["publishers"] = [timdex.Publisher(name=publisher.string)]
        else:
            logger.warning(
                "Datacite record %s missing required Datacite field publisher",
                source_record_id,
            )

        # related_items, uses related_identifiers retrieved for identifiers
        for related_identifier in [
            ri for ri in related_identifiers if ri.get("relationType") != "IsIdenticalTo"
        ]:
            fields.setdefault("related_items", []).append(
                timdex.RelatedItem(
                    uri=self.generate_related_item_identifier_url(related_identifier),
                    relationship=related_identifier.get("relationType")
                    or "Not specified",
                )
            )

        # rights
        for right in [
            r
            for r in source_record.metadata.find_all("rights")
            if r.string or r.get("rightsURI")
        ]:
            fields.setdefault("rights", []).append(
                timdex.Rights(
                    description=right.string or None, uri=right.get("rightsURI") or None
                )
            )

        # subjects
        subjects_dict: dict[str, list[str]] = {}
        for subject in source_record.metadata.find_all("subject", string=True):
            if not subject.get("subjectScheme"):
                subjects_dict.setdefault("Subject scheme not provided", []).append(
                    subject.string
                )
            else:
                subjects_dict.setdefault(subject["subjectScheme"], []).append(
                    subject.string
                )
        fields["subjects"] = [
            timdex.Subject(value=value, kind=key) for key, value in subjects_dict.items()
        ] or None

        # summary
        fields["summary"] = [
            d.string for d in descriptions if d.get("descriptionType") == "Abstract"
        ] or None

        return fields

    @classmethod
    def get_alternate_titles(
        cls, source_record: Tag
    ) -> list[timdex.AlternateTitle] | None:
        alternate_titles = []
        alternate_titles.extend(
            [
                timdex.AlternateTitle(
                    value=str(title.string.strip()),
                    kind=title["titleType"],
                )
                for title in source_record.find_all("title", string=True)
                if title.get("titleType")
            ]
        )
        alternate_titles.extend(list(cls._get_additional_titles(source_record)))
        return alternate_titles or None

    @classmethod
    def _get_additional_titles(
        cls, source_record: Tag
    ) -> Iterator[timdex.AlternateTitle]:
        """Get additional titles from get_main_titles method."""
        for index, title in enumerate(cls.get_main_titles(source_record)):
            if index > 0:
                yield timdex.AlternateTitle(value=title)

    @classmethod
    def get_content_type(
        cls, source_record: Tag, source_record_id: str
    ) -> list[str] | None:
        content_types = []
        if resource_type := source_record.metadata.find("resourceType"):
            if content_type := resource_type.get("resourceTypeGeneral"):
                if cls.valid_content_types([content_type]):
                    content_types.append(str(content_type))
                else:
                    message = f'Record skipped based on content type: "{content_type}"'
                    raise SkippedRecordEvent(message, source_record_id)
        else:
            logger.warning(
                "Datacite record %s missing required Datacite field resourceType",
                source_record_id,
            )
        return content_types or None

    @classmethod
    def get_contributors(cls, source_record: Tag) -> list[timdex.Contributor] | None:
        contributors = []
        contributors.extend(list(cls._get_creators(source_record)))
        contributors.extend(list(cls._get_contributors(source_record)))
        return contributors or None

    @classmethod
    def _get_creators(cls, source_record: Tag) -> Iterator[timdex.Contributor]:
        for creator in source_record.metadata.find_all("creator"):
            if creator_name := creator.find("creatorName", string=True):
                yield timdex.Contributor(
                    value=str(creator_name.string),
                    affiliation=[
                        str(affiliation.string)
                        for affiliation in creator.find_all("affiliation", string=True)
                    ]
                    or None,
                    identifier=[
                        cls.generate_name_identifier_url(name_identifier)
                        for name_identifier in creator.find_all(
                            "nameIdentifier", string=True
                        )
                    ]
                    or None,
                    kind="Creator",
                )

    @classmethod
    def _get_contributors(cls, source_record: Tag) -> Iterator[timdex.Contributor]:
        for contributor in source_record.metadata.find_all("contributor"):
            if contributor_name := contributor.find("contributorName", string=True):
                yield timdex.Contributor(
                    value=contributor_name.string,
                    affiliation=[
                        str(affiliation.string)
                        for affiliation in contributor.find_all(
                            "affiliation", string=True
                        )
                    ]
                    or None,
                    identifier=[
                        cls.generate_name_identifier_url(name_identifier)
                        for name_identifier in contributor.find_all(
                            "nameIdentifier", string=True
                        )
                    ]
                    or None,
                    kind=contributor.get("contributorType") or "Not specified",
                )

    @classmethod
    def get_main_titles(cls, source_record: Tag) -> list[str]:
        """
        Retrieve main title(s) from a Datacite XML record.

        Overrides metaclass get_main_titles() method.

        Args:
            source_record: A BeautifulSoup Tag representing a single Datacite record in
                oai_datacite XML.
        """
        return [
            str(title.string)
            for title in source_record.metadata.find_all("title", string=True)
            if not title.get("titleType")
        ]

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
    def valid_content_types(cls, _content_type_list: list[str]) -> bool:
        """
        Validate a list of content_type values from a Datacite XML record.

        May be overridden by source subclasses that require content type validation.

        Args:
            content_type_list: A list of content_type values.
        """
        return True
