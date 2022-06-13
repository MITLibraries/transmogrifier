"""DSpace METS XML transform module."""
import logging
from typing import Iterator

from bs4 import Tag

import transmogrifier.models as timdex
from transmogrifier.helpers import generate_citation

logger = logging.getLogger(__name__)


class DspaceMets:
    """DSpace METS transform class."""

    def __init__(
        self,
        source: str,
        source_base_url: str,
        source_name: str,
        input_records: Iterator[Tag],
    ) -> None:
        """
        Initialize DSpaceMets instance.

        Args:
            source: Source repository short label.
            source_base_url: Base URL for source repository records.
            source_name: Human-Readable full name of the source repository.
            input_records: Iterator of DSpace METS XML records.
        """
        self.source = source
        self.source_base_url = source_base_url
        self.source_name = source_name
        self.input_records = input_records

    def __iter__(self) -> Iterator[timdex.TimdexRecord]:
        """Iterate over records."""
        return self

    def __next__(self) -> timdex.TimdexRecord:
        """Return next transformed record in record iterator."""
        xml = next(self.input_records)
        record = self.create_from_dspace_mets_xml(
            self.source, self.source_base_url, self.source_name, xml
        )
        return record

    @classmethod
    def create_from_dspace_mets_xml(
        cls, source: str, source_base_url: str, source_name: str, xml: Tag
    ) -> timdex.TimdexRecord:
        """
        Create a TimdexRecord instance from a DSpace METS XML record.

        Args:
            source: A short label for the source repository.
            source_base_url: The base URL for the source system from which direct links
                to source metadata records can be constructed.
            source_name: The full human-readable name of the source repository to be
                used in the TIMDEX record.
            xml: A BeautifulSoup Tag representing a single DSpace record in METS XML.
        """

        # Required fields in TIMDEX
        source_record_id = xml.header.identifier.string.split(":")[2]
        all_titles = xml.metadata.find_all("mods:title")
        main_title = [t for t in all_titles if "type" not in t.attrs]
        if len(main_title) != 1:
            raise ValueError(
                f"A record must have exactly one title. {len(main_title)} titles found "
                f"for record {source_record_id}."
            )
        if not main_title[0].string:
            raise ValueError(
                f"Title field cannot be empty, record {source_record_id} had title "
                f"field value of '{main_title[0]}'"
            )
        kwargs = {
            "source": source_name,
            "source_link": f"{source_base_url}handle/{source_record_id}",
            "timdex_record_id": f"{source}:{source_record_id.replace('/', '-')}",
            "title": main_title[0].string,
        }

        # Optional fields in TIMDEX

        # alternate_titles
        # Uses full title list retrieved for main title field
        for alternate_title in [
            t for t in all_titles if "type" in t.attrs and t.string
        ]:
            kwargs.setdefault("alternate_titles", []).append(
                timdex.AlternateTitle(
                    value=alternate_title.string,
                    kind=alternate_title["type"],
                )
            )

        # call_numbers: relevant field in DSpace (dc.subject.classification) is not
        # mapped to the OAI-PMH METS output.

        # citation
        citation = xml.find("mods:identifier", type="citation")
        kwargs["citation"] = citation.string if citation and citation.string else None

        # content_type
        content_types = xml.find_all("mods:genre")
        kwargs["content_type"] = [
            content_type.string for content_type in content_types if content_type.string
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
                kwargs.setdefault("contributors", []).append(
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
            kwargs["dates"] = [
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
                kwargs.setdefault("file_formats", []).append(file["MIMETYPE"])

        # format
        kwargs["format"] = "electronic resource"

        # funding_information: relevant field in DSpace (dc.description.sponsorship) is
        # not mapped to the OAI-PMH METS output.

        # holdings field not used in DSpace

        # identifiers
        # Exludes citation because we have a separate field for that
        identifiers = xml.find_all("mods:identifier")
        for identifier in [
            i for i in identifiers if i.get("type") != "citation" and i.string
        ]:
            kwargs.setdefault("identifiers", []).append(
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
                kwargs.setdefault("languages", []).append(language_term.string)

        # links
        links = xml.find_all("mods:identifier", type="uri")
        kwargs["links"] = [
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
        kwargs["numbering"] = (
            numbering.string if numbering and numbering.string else None
        )

        # physical_description: relevant fields in DSpace (dc.format, dc.format.extent,
        # dc.format.medium) are not mapped to the OAI-PMH METS output.

        # publication_frequency field not used in DSpace

        # publication_information
        publication_information = xml.find_all("mods:publisher")
        kwargs["publication_information"] = [
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
            kwargs.setdefault("related_items", []).append(
                timdex.RelatedItem(
                    description=related_item.string,
                    relationship=related_item.get("type", "Relationship not specified"),
                )
            )

        # rights
        # Note: rights uri field in DSpace (dc.rights.uri) is not mapped to the OAI-PMH
        # METS output.
        rights = xml.find_all("mods:accessCondition")
        kwargs["rights"] = [
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
        kwargs["subjects"] = (
            [timdex.Subject(kind="Subject scheme not provided", value=subject_values)]
            if subject_values
            else None
        )

        # summary
        summaries = xml.find_all("mods:abstract")
        kwargs["summary"] = [
            summary.string for summary in summaries if summary.string
        ] or None

        # If citation field was not present, generate citation from other fields
        if kwargs.get("citation") is None:
            kwargs["citation"] = generate_citation(kwargs)

        return timdex.TimdexRecord(**kwargs)
