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
        for alternate_title in [
            t for t in xml.find_all("mods:title", string=True) if t.get("type")
        ]:
            fields.setdefault("alternate_titles", []).append(
                timdex.AlternateTitle(
                    value=alternate_title.string,
                    kind=alternate_title["type"],
                )
            )
        # If the record has more than one main title, add extras to alternate_titles
        for index, title in enumerate(self.get_main_titles(xml)):
            if index > 0:
                fields.setdefault("alternate_titles", []).append(
                    timdex.AlternateTitle(value=title.string)
                )

        # call_numbers: relevant field in DSpace (dc.subject.classification) is not
        # mapped to the OAI-PMH METS output.

        # citation
        if citation := xml.find("mods:identifier", type="citation", string=True):
            fields["citation"] = citation.string

        # content_type
        fields["content_type"] = [
            content_type.string
            for content_type in xml.find_all("mods:genre", string=True)
        ] or None

        # contents: relevant field in DSpace (dc.description.tableofcontents) is not
        # mapped to the OAI-PMH METS output.

        # contributors
        for contributor in xml.find_all("mods:name"):
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
        if publication_date := xml.find("mods:dateIssued", string=True):
            fields["dates"] = [
                timdex.Date(kind="Publication date", value=publication_date.string)
            ]

        # edition field not used in DSpace

        # file_formats
        # Only maps formats with attribute use="ORIGINAL" because other formats such as
        # USE="TEXT" are used internally by DSpace and not made publicly available.
        for file_group in xml.find_all("fileGrp", USE="ORIGINAL"):
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
            for i in xml.find_all("mods:identifier", string=True)
            if i.get("type") != "citation"
        ]:
            fields.setdefault("identifiers", []).append(
                timdex.Identifier(
                    kind=identifier.get("type") or "Not specified",
                    value=identifier.string,
                )
            )

        # languages
        for language in xml.find_all("mods:languageTerm", string=True):
            fields.setdefault("languages", []).append(language.string)

        # links
        for link in xml.find_all("mods:identifier", string=True, type="uri"):
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
        if numbering := xml.find("mods:relatedItem", string=True, type="series"):
            fields["numbering"] = numbering.string

        # physical_description: relevant fields in DSpace (dc.format, dc.format.extent,
        # dc.format.medium) are not mapped to the OAI-PMH METS output.

        # publication_frequency field not used in DSpace

        # publication_information
        for publisher in xml.find_all("mods:publisher", string=True):
            fields.setdefault("publication_information", []).append(publisher.string)

        # related_items
        # Excludes related items with type of "series" because the data in that field
        # seems to more accurately map to the numbering field.
        for related_item in [
            ri
            for ri in xml.find_all("mods:relatedItem", string=True)
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
        for right in xml.find_all("mods:accessCondition", string=True):
            fields.setdefault("rights", []).append(
                timdex.Rights(description=right.string, kind=right.get("type") or None)
            )

        # subjects
        # Note: subject fields with schemes in DSpace (dc.subject.<scheme>) are not
        # mapped to the OAI-PMH METS output.
        if topics := xml.find_all("mods:topic", string=True):
            fields["subjects"] = [
                timdex.Subject(
                    kind="Subject scheme not provided", value=[t.string for t in topics]
                )
            ]

        # summary
        fields["summary"] = [
            summary.string for summary in xml.find_all("mods:abstract", string=True)
        ] or None

        return fields

    @classmethod
    def get_main_titles(cls, xml: Tag) -> list[Tag]:
        """
        Retrieve main title(s) from a DSpace METS XML record.

        Overrides metaclass get_main_titles() method.

        Args:
            xml: A BeautifulSoup Tag representing a single DSpace METS XML record.
        """
        return [t for t in xml.find_all("mods:title", string=True) if not t.get("type")]

    @classmethod
    def get_source_record_id(cls, xml: Tag) -> str:
        """
        Get the source record ID from a DSpace METS XML record.

        Overrides metaclass get_source_record_id() method.

        Args:
            xml: A BeautifulSoup Tag representing a single DSpace METS XML record.
        """
        return xml.header.identifier.string.split(":")[2]
