"""DSpace METS XML transform module."""
import logging

from bs4 import Tag

import transmogrifier.models as timdex
from transmogrifier.sources.transformer import Transformer

logger = logging.getLogger(__name__)


class DspaceMets(Transformer):
    """DSpace METS transformer."""

    def get_optional_fields(self, xml: Tag) -> dict:
        """
        Retrieve optional TIMDEX fields from a DSpace METS XML record.

        Overrides metaclass get_optional_fields() method.

        Args:
            xml: A BeautifulSoup Tag representing a single DSpace METS XML record.
        """
        fields: dict = {}

        # alternate_titles
        # Uses full title list retrieved for main title field
        for alternate_title in [
            t for t in xml.find_all("mods:title") if "type" in t.attrs and t.string
        ]:
            fields.setdefault("alternate_titles", []).append(
                timdex.AlternateTitle(
                    value=alternate_title.string,
                    kind=alternate_title["type"],
                )
            )

        # call_numbers: relevant field in DSpace (dc.subject.classification) is not
        # mapped to the OAI-PMH METS output.

        # citation
        citation = xml.find("mods:identifier", type="citation")
        fields["citation"] = citation.string if citation and citation.string else None

        # content_type
        fields["content_type"] = [
            content_type.string
            for content_type in xml.find_all("mods:genre")
            if content_type.string
        ] or None

        # contents: relevant field in DSpace (dc.description.tableofcontents) is not
        # mapped to the OAI-PMH METS output.

        # contributors
        contributors = xml.find_all("mods:name")
        for contributor in contributors:
            name = contributor.find("mods:namePart")
            if name and name.string:
                if role_field := contributor.find("mods:role"):
                    role_name = role_field.find("mods:roleTerm")
                    kind = role_name.string or "Contributor role not specified"
                else:
                    kind = "Contributor role not specified"
                fields.setdefault("contributors", []).append(
                    timdex.Contributor(
                        kind=kind,
                        value=name.string,
                    )
                )

        # dates
        # Only publication date is mapped from DSpace, other relevant date field (dc.
        # coverage.temporal) is not mapped to the OAI-PMH METS output.
        publication_date = xml.find("mods:dateIssued")
        if publication_date and publication_date.string:
            fields["dates"] = [
                timdex.Date(kind="Publication date", value=publication_date.string)
            ]

        # edition field not used in DSpace

        # file_formats
        # Only maps formats with attribute use="ORIGINAL" because other formats such as
        # USE="TEXT" are used internally by DSpace and not made publicly available.
        file_groups = xml.find_all("fileGrp", USE="ORIGINAL")
        for file_group in file_groups:
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
        identifiers = xml.find_all("mods:identifier")
        for identifier in [
            i for i in identifiers if i.get("type") != "citation" and i.string
        ]:
            fields.setdefault("identifiers", []).append(
                timdex.Identifier(
                    kind=identifier.get("type", "Identifier kind not specified"),
                    value=identifier.string,
                )
            )

        # languages
        languages = xml.find_all("mods:language")
        for language in languages:
            language_term = language.find("mods:languageTerm")
            if language_term and language_term.string:
                fields.setdefault("languages", []).append(language_term.string)

        # links
        links = xml.find_all("mods:identifier", type="uri")
        fields["links"] = [
            timdex.Link(
                kind="Digital object URL",
                text="Digital object URL",
                url=link.string,
            )
            for link in links
            if link.string
        ] or None

        # literary_form field not used in DSpace

        # locations: relevant field in DSpace (dc.coverage.spatial) is not mapped to
        # the OAI-PMH METS output.

        # notes: relevant field in DSpace (unqualified dc.description) is not mapped to
        # the OAI-PMH METS output.

        # numbering
        numbering = xml.find("mods:relatedItem", type="series")
        fields["numbering"] = (
            numbering.string if numbering and numbering.string else None
        )

        # physical_description: relevant fields in DSpace (dc.format, dc.format.extent,
        # dc.format.medium) are not mapped to the OAI-PMH METS output.

        # publication_frequency field not used in DSpace

        # publication_information
        publication_information = xml.find_all("mods:publisher")
        fields["publication_information"] = [
            publisher.string
            for publisher in publication_information
            if publisher.string
        ] or None

        # related_items
        # Excludes related items with type of "series" because the data in that field
        # seems to more accurately map to the numbering field.
        related_items = xml.find_all("mods:relatedItem")
        for related_item in [
            ri for ri in related_items if ri.get("type") != "series" and ri.string
        ]:
            fields.setdefault("related_items", []).append(
                timdex.RelatedItem(
                    description=related_item.string,
                    relationship=related_item.get("type", "Relationship not specified"),
                )
            )

        # rights
        # Note: rights uri field in DSpace (dc.rights.uri) is not mapped to the OAI-PMH
        # METS output.
        rights = xml.find_all("mods:accessCondition")
        fields["rights"] = [
            timdex.Rights(description=right.string, kind=right.get("type"))
            for right in rights
            if right.string
        ] or None

        # subjects
        # Note: subject fields with schemes in DSpace (dc.subject.<scheme>) are not
        # mapped to the OAI-PMH METS output.
        subjects = xml.find_all("mods:subject")
        subject_values: list[str] = []
        for subject in subjects:
            topic = subject.find("mods:topic")
            if topic and topic.string:
                subject_values.append(topic.string)
        fields["subjects"] = (
            [timdex.Subject(kind="Subject scheme not provided", value=subject_values)]
            if subject_values
            else None
        )

        # summary
        summaries = xml.find_all("mods:abstract")
        fields["summary"] = [
            summary.string for summary in summaries if summary.string
        ] or None

        return fields

    @classmethod
    def get_main_titles(cls, xml: Tag) -> list[str]:
        """
        Retrieve main title(s) from a DSpace METS XML record.

        Overrides metaclass get_main_titles() method.

        Args:
            xml: A BeautifulSoup Tag representing a single DSpace METS XML record.
        """
        return [t for t in xml.find_all("mods:title") if "type" not in t.attrs]

    @classmethod
    def get_source_record_id(cls, xml) -> str:
        """
        Get the source record ID from a DSpace METS XML record.

        Overrides metaclass get_source_record_id() method.

        Args:
            xml: A BeautifulSoup Tag representing a single DSpace METS XML record.
        """
        return xml.header.identifier.string.split(":")[2]
