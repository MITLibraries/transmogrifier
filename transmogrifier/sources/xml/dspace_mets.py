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

        source_record_id = self.get_source_record_id(source_record)

        # alternate_titles
        fields["alternate_titles"] = self.get_alternate_titles(source_record)

        # citation
        fields["citation"] = self.get_citation(source_record)

        # content_type
        fields["content_type"] = self.get_content_type(source_record)

        # contents: relevant field in DSpace (dc.description.tableofcontents) is not
        # mapped to the OAI-PMH METS output.

        # contributors
        for contributor in source_record.find_all("mods:name"):
            if name := contributor.find("mods:namePart", string=True):
                if role := contributor.find("mods:roleTerm", string=True):
                    kind = role.string
                else:
                    kind = "Not specified"
                fields.setdefault("contributors", []).append(
                    timdex.Contributor(
                        kind=kind,
                        value=name.string,
                    )
                )

        # dates
        # Only publication date is mapped from DSpace, other relevant date field (dc.
        # coverage.temporal) is not mapped to the OAI-PMH METS output.
        if publication_date := source_record.find("mods:dateIssued", string=True):
            publication_date_value = str(publication_date.string.strip())
            if validate_date(publication_date_value, source_record_id):
                fields["dates"] = [
                    timdex.Date(kind="Publication date", value=publication_date_value)
                ]

        # edition field not used in DSpace

        # file_formats
        # Only maps formats with attribute use="ORIGINAL" because other formats such as
        # USE="TEXT" are used internally by DSpace and not made publicly available.
        for file_group in source_record.find_all("fileGrp", USE="ORIGINAL"):
            file = file_group.find("file")
            if file and file.get("MIMETYPE"):
                fields.setdefault("file_formats", []).append(file["MIMETYPE"])

        # format
        fields["format"] = "electronic resource"

        # funding_information: relevant field in DSpace (dc.description.sponsorship) is
        # not mapped to the OAI-PMH METS output.

        # holdings field not used in DSpace

        # identifiers
        # Exludes citation because we have a separate field for that
        for identifier in [
            i
            for i in source_record.find_all("mods:identifier", string=True)
            if i.get("type") != "citation"
        ]:
            fields.setdefault("identifiers", []).append(
                timdex.Identifier(
                    kind=identifier.get("type") or "Not specified",
                    value=identifier.string,
                )
            )

        # languages
        for language in source_record.find_all("mods:languageTerm", string=True):
            fields.setdefault("languages", []).append(language.string)

        # links
        for link in source_record.find_all("mods:identifier", string=True, type="uri"):
            fields.setdefault("links", []).append(
                timdex.Link(
                    kind="Digital object URL",
                    text="Digital object URL",
                    url=link.string,
                )
            )

        # literary_form field not used in DSpace

        # locations: relevant field in DSpace (dc.coverage.spatial) is not mapped to
        # the OAI-PMH METS output.

        # notes: relevant field in DSpace (unqualified dc.description) is not mapped to
        # the OAI-PMH METS output.

        # numbering
        if numbering := source_record.find(
            "mods:relatedItem", string=True, type="series"
        ):
            fields["numbering"] = numbering.string

        # physical_description: relevant fields in DSpace (dc.format, dc.format.extent,
        # dc.format.medium) are not mapped to the OAI-PMH METS output.

        # publication_frequency field not used in DSpace

        # publishers
        for publisher in source_record.find_all("mods:publisher", string=True):
            fields.setdefault("publishers", []).append(
                timdex.Publisher(name=publisher.string)
            )

        # related_items
        # Excludes related items with type of "series" because the data in that field
        # seems to more accurately map to the numbering field.
        for related_item in [
            ri
            for ri in source_record.find_all("mods:relatedItem", string=True)
            if ri.get("type") != "series"
        ]:
            fields.setdefault("related_items", []).append(
                timdex.RelatedItem(
                    description=related_item.string,
                    relationship=related_item.get("type") or "Not specified",
                )
            )

        # rights
        # Note: rights uri field in DSpace (dc.rights.uri) is not mapped to the OAI-PMH
        # METS output.
        for right in source_record.find_all("mods:accessCondition", string=True):
            fields.setdefault("rights", []).append(
                timdex.Rights(description=right.string, kind=right.get("type") or None)
            )

        # subjects
        # Note: subject fields with schemes in DSpace (dc.subject.<scheme>) are not
        # mapped to the OAI-PMH METS output.
        if topics := source_record.find_all("mods:topic", string=True):
            fields["subjects"] = [
                timdex.Subject(
                    kind="Subject scheme not provided", value=[t.string for t in topics]
                )
            ]

        # summary
        fields["summary"] = [
            summary.string
            for summary in source_record.find_all("mods:abstract", string=True)
        ] or None

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
        for index, title in enumerate(cls.get_main_titles(source_record)):
            if index > 0:
                alternate_titles.append(timdex.AlternateTitle(value=title))
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
    def get_main_titles(cls, source_record: Tag) -> list[str]:
        """
        Retrieve main title(s) from a DSpace METS XML record.

        Overrides metaclass get_main_titles() method.

        Args:
            source_record: A BeautifulSoup Tag representing a single DSpace METS XML
            record.
        """
        return [
            t.string
            for t in source_record.find_all("mods:title", string=True)
            if not t.get("type")
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
