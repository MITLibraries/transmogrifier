"""DSpace METS XML transform module."""

import logging

from bs4 import Tag  # type: ignore[import-untyped]

import transmogrifier.models as timdex
from transmogrifier.helpers import validate_date
from transmogrifier.sources.xmltransformer import XMLTransformer

logger = logging.getLogger(__name__)


class DspaceMets(XMLTransformer):
    """DSpace METS transformer."""

    def get_optional_fields(self, source_record: Tag) -> dict:
        """
        Retrieve optional TIMDEX fields from a DSpace METS XML record.

        Overrides metaclass get_optional_fields() method.

        Args:
            source_record: A BeautifulSoup Tag representing a single DSpace METS XML
            record.
        """
        fields: dict = {}

        # alternate_titles
        fields["alternate_titles"] = self.get_alternate_titles(source_record)

        # citation
        fields["citation"] = self.get_citation(source_record)

        # content_type
        fields["content_type"] = self.get_content_type(source_record)

        # contents: relevant field in DSpace (dc.description.tableofcontents) is not
        # mapped to the OAI-PMH METS output.

        # contributors
        fields["contributors"] = self.get_contributors(source_record)

        # dates
        fields["dates"] = self.get_dates(source_record)

        # edition field not used in DSpace

        # file_formats
        fields["file_formats"] = self.get_file_formats(source_record)

        # format
        fields["format"] = self.get_format()

        # funding_information: relevant field in DSpace (dc.description.sponsorship) is
        # not mapped to the OAI-PMH METS output.

        # holdings field not used in DSpace

        # identifiers
        # Exludes citation because we have a separate field for that
        fields["identifiers"] = self.get_identifiers(source_record)

        # languages
        fields["languages"] = self.get_languages(source_record)

        # links
        fields["links"] = self.get_links(source_record)

        # literary_form field not used in DSpace

        # locations: relevant field in DSpace (dc.coverage.spatial) is not mapped to
        # the OAI-PMH METS output.

        # notes: relevant field in DSpace (unqualified dc.description) is not mapped to
        # the OAI-PMH METS output.

        # numbering
        fields["numbering"] = self.get_numbering(source_record)

        # physical_description: relevant fields in DSpace (dc.format, dc.format.extent,
        # dc.format.medium) are not mapped to the OAI-PMH METS output.

        # publication_frequency field not used in DSpace

        # publishers
        fields["publishers"] = self.get_publishers(source_record)

        # related_items
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
                value=str(alternate_title.string),
                kind=alternate_title["type"],
            )
            for alternate_title in source_record.find_all("mods:title", string=True)
            if alternate_title.get("type")
        ]
        # If the record has more than one main title, add extras to alternate_titles
        alternate_titles.extend(
            [
                timdex.AlternateTitle(value=title)
                for title in cls.get_main_titles(source_record)[1:]
            ]
        )
        return alternate_titles or None

    @classmethod
    def get_citation(cls, source_record: Tag) -> str | None:
        if citation := source_record.find(
            "mods:identifier", type="citation", string=True
        ):
            return str(citation.string)
        return None

    @classmethod
    def get_content_type(cls, source_record: Tag) -> list[str] | None:
        return [
            str(content_type.string)
            for content_type in source_record.find_all("mods:genre", string=True)
        ] or None

    @classmethod
    def get_contributors(cls, source_record: Tag) -> list[timdex.Contributor] | None:
        contributors = []
        for contributor in source_record.find_all("mods:name"):
            if name := contributor.find("mods:namePart", string=True):
                if role := contributor.find("mods:roleTerm", string=True):
                    kind = str(role.string)
                else:
                    kind = "Not specified"
                contributors.append(
                    timdex.Contributor(
                        kind=kind,
                        value=str(name.string),
                    )
                )
        return contributors or None

    @classmethod
    def get_dates(cls, source_record: Tag) -> list[timdex.Date] | None:
        # Only publication date is mapped from DSpace, other relevant date field (dc.
        # coverage.temporal) is not mapped to the OAI-PMH METS output.
        if publication_date := source_record.find("mods:dateIssued", string=True):
            publication_date_value = str(publication_date.string.strip())
            if validate_date(
                publication_date_value, cls.get_source_record_id(source_record)
            ):
                return [
                    timdex.Date(kind="Publication date", value=publication_date_value)
                ]
        return None

    @classmethod
    def get_file_formats(cls, source_record: Tag) -> list[str] | None:
        # Only maps formats with attribute use="ORIGINAL" because other formats such as
        # USE="TEXT" are used internally by DSpace and not made publicly available.
        file_formats = []
        for file_group in source_record.find_all("fileGrp", USE="ORIGINAL"):
            file = file_group.find("file")
            if file and file.get("MIMETYPE"):
                file_formats.append(file["MIMETYPE"])
        return file_formats or None

    @classmethod
    def get_format(cls) -> str:
        return "electronic resource"

    @classmethod
    def get_identifiers(cls, source_record: Tag) -> list[timdex.Identifier] | None:
        return [
            timdex.Identifier(
                kind=identifier.get("type") or "Not specified",
                value=str(identifier.string),
            )
            for identifier in source_record.find_all("mods:identifier", string=True)
            if identifier.get("type") != "citation"
        ] or None

    @classmethod
    def get_languages(cls, source_record: Tag) -> list[str] | None:
        return [
            str(language.string)
            for language in source_record.find_all("mods:languageTerm", string=True)
        ] or None

    @classmethod
    def get_links(cls, source_record: Tag) -> list[timdex.Link] | None:
        return [
            timdex.Link(
                kind="Digital object URL",
                text="Digital object URL",
                url=str(link.string),
            )
            for link in source_record.find_all("mods:identifier", string=True, type="uri")
        ] or None

    @classmethod
    def get_numbering(cls, source_record: Tag) -> str | None:
        if numbering := source_record.find(
            "mods:relatedItem", string=True, type="series"
        ):
            return str(numbering.string)
        return None

    @classmethod
    def get_publishers(cls, source_record: Tag) -> list[timdex.Publisher] | None:
        return [
            timdex.Publisher(name=str(publisher.string))
            for publisher in source_record.find_all("mods:publisher", string=True)
        ] or None

    @classmethod
    def get_related_items(cls, source_record: Tag) -> list[timdex.RelatedItem] | None:
        return [
            timdex.RelatedItem(
                description=str(related_item.string),
                relationship=related_item.get("type") or "Not specified",
            )
            for related_item in source_record.find_all("mods:relatedItem", string=True)
            if related_item.get("type") != "series"
        ] or None

    @classmethod
    def get_rights(cls, source_record: Tag) -> list[timdex.Rights] | None:
        # Note: rights uri field in DSpace (dc.rights.uri) is not mapped to the OAI-PMH
        # METS output.
        return [
            timdex.Rights(description=str(right.string), kind=right.get("type") or None)
            for right in source_record.find_all("mods:accessCondition", string=True)
        ] or None

    @classmethod
    def get_subjects(cls, source_record: Tag) -> list[timdex.Subject] | None:
        # Note: subject fields with schemes in DSpace (dc.subject.<scheme>) are not
        # mapped to the OAI-PMH METS output.
        if subjects := source_record.find_all("mods:topic", string=True):
            return [
                timdex.Subject(
                    kind="Subject scheme not provided",
                    value=[str(subject.string) for subject in subjects],
                )
            ]
        return None

    @classmethod
    def get_summary(cls, source_record: Tag) -> list[str] | None:
        return [
            str(summary.string)
            for summary in source_record.find_all("mods:abstract", string=True)
        ] or None

    @classmethod
    def get_main_titles(cls, source_record: Tag) -> list[str]:
        """
        Retrieve main title(s) from a DSpace METS XML record.

        Overrides metaclass get_main_titles() method.

        Args:
            source_record: A BeautifulSoup Tag representing a single DSpace METS XML
            record.
        """
        return [
            str(title.string)
            for title in source_record.find_all("mods:title", string=True)
            if not title.get("type")
        ]

    @classmethod
    def get_source_record_id(cls, source_record: Tag) -> str:
        """
        Get the source record ID from a DSpace METS XML record.

        Overrides metaclass get_source_record_id() method.

        Args:
            source_record: A BeautifulSoup Tag representing a single DSpace METS XML
            record.
        """
        return source_record.header.identifier.string.split(":")[2]
