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

        # alternate_titles
        fields["alternate_titles"] = self.get_alternate_titles(source_record)

        # content_type
        fields["content_type"] = self.get_content_type(source_record)

        # contributors
        fields["contributors"] = self.get_contributors(source_record)

        # dates
        fields["dates"] = self.get_dates(source_record)

        # edition
        fields["edition"] = self.get_edition(source_record)

        # file_formats
        fields["file_formats"] = self.get_file_formats(source_record)

        # format
        fields["format"] = self.get_format()

        # funding_information
        fields["funding_information"] = self.get_funding_information(source_record)

        # identifiers
        fields["identifiers"] = self.get_identifiers(source_record)

        # languages
        fields["languages"] = self.get_languages(source_record)

        # links
        fields["links"] = self.get_links(source_record)

        # locations
        fields["locations"] = self.get_locations(source_record)

        # notes
        fields["notes"] = self.get_notes(source_record)

        # publishers
        fields["publishers"] = self.get_publishers(source_record)

        # related_items, uses related_identifiers retrieved for identifiers
        fields["related_items"] = self.get_related_items(source_record)

        # rights
        fields["rights"] = self.get_rights(source_record)

        # subjects
        fields["subjects"] = self.get_subjects(source_record)

        # summary
        fields["summary"] = self.get_summary(source_record)

        return fields

    @classmethod
    def get_alternate_titles(
        cls, source_record: Tag
    ) -> list[timdex.AlternateTitle] | None:
        alternate_titles = [
            timdex.AlternateTitle(
                value=str(title.string.strip()),
                kind=title["titleType"],
            )
            for title in source_record.find_all("title", string=True)
            if title.get("titleType")
        ]
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
    def get_content_type(cls, source_record: Tag) -> list[str] | None:
        content_types = []
        if resource_type := source_record.metadata.find("resourceType"):
            if content_type := resource_type.get("resourceTypeGeneral"):
                if cls.valid_content_types([content_type]):
                    content_types.append(str(content_type))
                else:
                    message = f'Record skipped based on content type: "{content_type}"'
                    raise SkippedRecordEvent(
                        message, cls.get_source_record_id(source_record)
                    )
        else:
            logger.warning(
                "Datacite record %s missing required Datacite field resourceType",
                cls.get_source_record_id(source_record),
            )
        return content_types or None

    @classmethod
    def get_contributors(cls, source_record: Tag) -> list[timdex.Contributor] | None:
        contributors = []
        contributors.extend(list(cls._get_creators(source_record)))
        contributors.extend(
            list(cls._get_contributors_by_contributor_element(source_record))
        )
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
    def _get_contributors_by_contributor_element(
        cls, source_record: Tag
    ) -> Iterator[timdex.Contributor]:
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
    def get_dates(
        cls,
        source_record: Tag,
    ) -> list[timdex.Date] | None:
        dates = []
        dates.extend(list(cls._get_publication_year(source_record)))
        dates.extend(list(cls._get_dates_by_date_element(source_record)))
        return dates or None

    @classmethod
    def _get_publication_year(cls, source_record: Tag) -> Iterator[timdex.Date]:
        if publication_year := source_record.metadata.find(
            "publicationYear", string=True
        ):
            publication_year = str(publication_year.string.strip())
            if validate_date(
                publication_year,
                cls.get_source_record_id(source_record),
            ):
                yield timdex.Date(kind="Publication date", value=publication_year)
        else:
            logger.warning(
                "Datacite record %s missing required Datacite field publicationYear",
                cls.get_source_record_id(source_record),
            )

    @classmethod
    def _get_dates_by_date_element(cls, source_record: Tag) -> Iterator[timdex.Date]:
        for date_element in source_record.metadata.find_all("date"):
            date_object = timdex.Date()
            if date_value := date_element.string:
                date_value = str(date_value)
                if "/" in date_value:
                    date_object = cls._parse_date_range(
                        date_object, date_value, cls.get_source_record_id(source_record)
                    )
                else:
                    date_object.value = (
                        date_value.strip()
                        if validate_date(
                            date_value,
                            cls.get_source_record_id(source_record),
                        )
                        else None
                    )
            date_object.note = date_element.get("dateInformation") or None
            if any([date_object.note, date_object.range, date_object.value]):
                date_object.kind = date_element.get("dateType") or None
                yield date_object

    @classmethod
    def _parse_date_range(
        cls, date_object: timdex.Date, date_value: str, source_record_id: str
    ) -> timdex.Date:
        split = date_value.index("/")
        gte_date = date_value[:split].strip()
        lte_date = date_value[split + 1 :].strip()
        if validate_date_range(
            gte_date,
            lte_date,
            source_record_id,
        ):
            date_object.range = timdex.DateRange(
                gte=gte_date,
                lte=lte_date,
            )
        return date_object

    @classmethod
    def get_edition(cls, source_record: Tag) -> str | None:
        if edition := source_record.metadata.find("version", string=True):
            return str(edition.string)
        return None

    @classmethod
    def get_file_formats(cls, source_record: Tag) -> list[str] | None:
        return [
            str(file_format.string)
            for file_format in source_record.metadata.find_all("format", string=True)
        ] or None

    @classmethod
    def get_format(cls) -> str:
        return "electronic resource"

    @classmethod
    def get_funding_information(cls, source_record: Tag) -> list[timdex.Funder] | None:
        funding_information = []
        for funding_reference in source_record.metadata.find_all("fundingReference"):
            funder = timdex.Funder()
            if funder_name := funding_reference.find("funderName", string=True):
                funder.funder_name = str(funder_name.string)
            if award_number := funding_reference.find("awardNumber"):
                funder.award_number = award_number.string or None
                funder.award_uri = award_number.get("awardURI") or None
            if funder_identifier := funding_reference.find(
                "funderIdentifier", string=True
            ):
                funder.funder_identifier = str(funder_identifier.string)
                funder.funder_identifier_type = (
                    funder_identifier.get("funderIdentifierType") or None
                )
            if funder != timdex.Funder():
                funding_information.append(funder)
        return funding_information or None

    @classmethod
    def get_identifiers(
        cls,
        source_record: Tag,
    ) -> list[timdex.Identifier] | None:
        identifiers = []
        if identifier_element := source_record.metadata.find("identifier", string=True):
            identifiers.append(
                timdex.Identifier(
                    value=str(identifier_element.string),
                    kind=identifier_element.get("identifierType") or "Not specified",
                )
            )
        identifiers.extend(list(cls._get_alternate_identifiers(source_record)))
        identifiers.extend(list(cls._get_related_identifiers(source_record)))
        return identifiers or None

    @classmethod
    def _get_alternate_identifiers(
        cls,
        source_record: Tag,
    ) -> Iterator[timdex.Identifier]:
        for alternate_identifier_element in source_record.metadata.find_all(
            "alternateIdentifier", string=True
        ):
            yield timdex.Identifier(
                value=str(alternate_identifier_element.string),
                kind=alternate_identifier_element.get("alternateIdentifierType")
                or "Not specified",
            )

    @classmethod
    def _get_related_identifiers(
        cls,
        source_record: Tag,
    ) -> Iterator[timdex.Identifier]:
        related_identifier_elements = source_record.metadata.find_all(
            "relatedIdentifier", string=True
        )
        for related_identifier_element in [
            related_identifier_element
            for related_identifier_element in related_identifier_elements
            if related_identifier_element.get("relationType") == "IsIdenticalTo"
        ]:
            yield timdex.Identifier(
                value=cls.generate_related_item_identifier_url(
                    related_identifier_element
                ),
                kind=str(related_identifier_element["relationType"]),
            )

    @classmethod
    def get_languages(cls, source_record: Tag) -> list[str] | None:
        languages = []
        if language := source_record.metadata.find("language", string=True):
            languages.append(str(language.string))
        return languages or None

    def get_links(self, source_record: Tag) -> list[timdex.Link] | None:
        return [
            timdex.Link(
                kind="Digital object URL",
                text="Digital object URL",
                url=self.source_base_url + self.get_source_record_id(source_record),
            )
        ]

    @classmethod
    def get_locations(cls, source_record: Tag) -> list[timdex.Location] | None:
        return [
            timdex.Location(value=str(location.string))
            for location in source_record.metadata.find_all(
                "geoLocationPlace", string=True
            )
        ] or None

    @classmethod
    def get_notes(cls, source_record: Tag) -> list[timdex.Note] | None:
        notes = []
        notes.extend(list(cls._get_resource_type_note(source_record)))
        notes.extend(list(cls._get_description_notes(source_record)))
        return notes or None

    @classmethod
    def _get_resource_type_note(cls, source_record: Tag) -> Iterator[timdex.Note]:
        if resource_type := source_record.metadata.find("resourceType", string=True):
            yield timdex.Note(
                value=[str(resource_type.string)],
                kind="Datacite resource type",
            )

    @classmethod
    def _get_description_notes(cls, source_record: Tag) -> Iterator[timdex.Note]:
        descriptions = source_record.metadata.find_all("description", string=True)
        for description in descriptions:
            if "descriptionType" not in description.attrs:
                logger.warning(
                    "Datacite record %s missing required Datacite attribute "
                    "@descriptionType",
                    cls.get_source_record_id(source_record),
                )
            if description.get("descriptionType") != "Abstract":
                yield timdex.Note(
                    value=[str(description.string)],
                    kind=description.get("descriptionType") or None,
                )

    @classmethod
    def get_publishers(cls, source_record: Tag) -> list[timdex.Publisher] | None:
        publishers = []
        if publisher := source_record.metadata.find("publisher", string=True):
            publishers.append(timdex.Publisher(name=str(publisher.string)))
        else:
            logger.warning(
                "Datacite record %s missing required Datacite field publisher",
                cls.get_source_record_id(source_record),
            )
        return publishers or None

    @classmethod
    def get_related_items(cls, source_record: Tag) -> list[timdex.RelatedItem] | None:
        return [
            timdex.RelatedItem(
                uri=cls.generate_related_item_identifier_url(related_identifier),
                relationship=related_identifier.get("relationType") or "Not specified",
            )
            for related_identifier in source_record.metadata.find_all(
                "relatedIdentifier", string=True
            )
            if related_identifier.get("relationType") != "IsIdenticalTo"
        ] or None

    @classmethod
    def get_rights(cls, source_record: Tag) -> list[timdex.Rights] | None:
        return [
            timdex.Rights(
                description=rights.string or None,
                uri=rights.get("rightsURI") or None,
            )
            for rights in source_record.metadata.find_all("rights")
            if rights.string or rights.get("rightsURI")
        ] or None

    @classmethod
    def get_subjects(cls, source_record: Tag) -> list[timdex.Subject] | None:
        subjects_dict: dict[str, list[str]] = {}

        for subject in source_record.metadata.find_all("subject", string=True):
            if not subject.get("subjectScheme"):
                subjects_dict.setdefault("Subject scheme not provided", []).append(
                    str(subject.string)
                )
            else:
                subjects_dict.setdefault(subject["subjectScheme"], []).append(
                    str(subject.string)
                )

        return [
            timdex.Subject(value=subject_value, kind=subject_scheme)
            for subject_scheme, subject_value in subjects_dict.items()
        ] or None

    @classmethod
    def get_summary(cls, source_record: Tag) -> list[str] | None:
        return [
            str(description.string)
            for description in source_record.metadata.find_all("description", string=True)
            if description.get("descriptionType") == "Abstract"
        ] or None

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
