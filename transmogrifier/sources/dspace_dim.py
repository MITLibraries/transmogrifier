import logging
from typing import Dict, List, Optional

from bs4 import Tag

import transmogrifier.models as timdex
from transmogrifier.helpers import validate_date, validate_date_range
from transmogrifier.sources.transformer import Transformer

logger = logging.getLogger(__name__)


class DspaceDim(Transformer):
    """DSpace DIM transformer."""

    def get_optional_fields(self, xml: Tag) -> Optional[dict]:
        """
        Retrieve optional TIMDEX fields from a DSpace DIM XML record.

        Overrides metaclass get_optional_fields() method.

        Args:
            xml: A BeautifulSoup Tag representing a single DSpace DIM XML record.
        """
        fields: dict = {}

        source_record_id = self.get_source_record_id(xml)

        # alternate_titles
        for alternate_title in [
            t
            for t in xml.find_all("dim:field", element="title")
            if "qualifier" in t.attrs and t.string
        ]:
            fields.setdefault("alternate_titles", []).append(
                timdex.AlternateTitle(
                    value=alternate_title.string,
                    kind=alternate_title["qualifier"] or None,
                )
            )
        # If the record has more than one main title, add extras to alternate_titles
        for index, title in enumerate(self.get_main_titles(xml)):
            if index > 0:
                fields.setdefault("alternate_titles", []).append(
                    timdex.AlternateTitle(value=title.string)
                )

        # citation
        citation = xml.find("dim:field", element="identifier", qualifier="citation")
        fields["citation"] = citation.string if citation and citation.string else None

        # content_type
        if content_types := self.get_content_types(xml):
            if self.valid_content_types(content_types):
                fields["content_type"] = content_types
            else:
                return None

        # contents
        fields["contents"] = [
            t.string
            for t in xml.find_all(
                "dim:field", element="description", qualifier="tableofcontents"
            )
            if t.string
        ] or None

        # contributors
        for creator in [
            c for c in xml.find_all("dim:field", element="creator") if c.string
        ]:
            fields.setdefault("contributors", []).append(
                timdex.Contributor(
                    value=creator.string,
                    kind="Creator",
                )
            )

        for contributor in [
            c for c in xml.find_all("dim:field", element="contributor") if c.string
        ]:
            fields.setdefault("contributors", []).append(
                timdex.Contributor(
                    value=contributor.string,
                    kind=contributor.get("qualifier") or "Not specified",
                )
            )

        # dates
        for date in [d for d in xml.find_all("dim:field", element="date") if d.string]:
            date_value = str(date.string.strip())
            if validate_date(date_value, source_record_id):
                if date.get("qualifier") == "issued":
                    d = timdex.Date(value=date_value, kind="Publication date")
                else:
                    d = timdex.Date(
                        value=date_value, kind=date.get("qualifier") or None
                    )
                fields.setdefault("dates", []).append(d)

        for coverage in [
            c.string
            for c in xml.find_all("dim:field", element="coverage", qualifier="temporal")
            if c.string
        ]:
            if "/" in coverage:
                split = coverage.index("/")
                gte_date = coverage[:split]
                lte_date = coverage[split + 1 :]
                if validate_date_range(
                    gte_date,
                    lte_date,
                    source_record_id,
                ):
                    d = timdex.Date(
                        range=timdex.Date_Range(
                            gte=gte_date,
                            lte=lte_date,
                        ),
                        kind="coverage",
                    )
            else:
                d = timdex.Date(note=coverage.string, kind="coverage")
            fields.setdefault("dates", []).append(d)

        # file_formats
        fields["file_formats"] = [
            f.string
            for f in xml.find_all("dim:field", element="format")
            if f.get("qualifier") == "mimetype" and f.string
        ] or None

        # format
        fields["format"] = "electronic resource"

        # funding_information
        for funding_reference in [
            f
            for f in xml.find_all(
                "dim:field", element="description", qualifier="sponsorship"
            )
            if f.string
        ]:
            fields.setdefault("funding_information", []).append(
                timdex.Funder(
                    funder_name=funding_reference.string,
                )
            )

        # identifiers
        identifiers = xml.find_all("dim:field", element="identifier")
        for identifier in [
            i for i in identifiers if i.get("qualifier") != "citation" and i.string
        ]:
            fields.setdefault("identifiers", []).append(
                timdex.Identifier(
                    value=identifier.string,
                    kind=identifier.get("qualifier") or "Not specified",
                )
            )

        # language
        fields["languages"] = [
            la.string
            for la in xml.find_all("dim:field", element="language")
            if la.string
        ] or None

        # links, uses identifiers list retrieved for identifiers field
        fields["links"] = [
            timdex.Link(
                kind="Digital object URL",
                text="Digital object URL",
                url=identifier.string,
            )
            for identifier in [
                i for i in identifiers if i.get("qualifier") == "uri" and i.string
            ]
        ] or None

        # locations
        fields["locations"] = [
            timdex.Location(value=lo.string)
            for lo in xml.find_all("dim:field", element="coverage", qualifier="spatial")
            if lo.string
        ] or None

        # notes
        descriptions = xml.find_all("dim:field", element="description")
        for description in [
            d
            for d in descriptions
            if d.get("qualifier")
            not in [
                "abstract",
                "provenance",
                "sponsorship",
                "tableofcontents",
            ]
            and d.string
        ]:
            fields.setdefault("notes", []).append(
                timdex.Note(
                    value=[description.string],
                    kind=description.get("qualifier") or None,
                )
            )

        # publication_information
        fields["publication_information"] = [
            p.string for p in xml.find_all("dim:field", element="publisher") if p.string
        ] or None

        # related_items
        for related_item in [
            r for r in xml.find_all("dim:field", element="relation") if r.string
        ]:
            if related_item.get("qualifier") == "uri":
                ri = timdex.RelatedItem(
                    uri=related_item.string, relationship="Not specified"
                )
            else:
                ri = timdex.RelatedItem(
                    description=related_item.string,
                    relationship=related_item.get("qualifier") or "Not specified",
                )
            fields.setdefault("related_items", []).append(ri)

        # rights
        for rights in [
            r for r in xml.find_all("dim:field", element="rights") if r.string
        ]:
            if rights.get("qualifier") == "uri":
                rg = timdex.Rights(uri=rights.string)
            else:
                rg = timdex.Rights(
                    description=rights.string, kind=rights.get("qualifier") or None
                )
            fields.setdefault("rights", []).append(rg)

        # subjects
        subjects_dict: Dict[str, List[str]] = {}
        for subject in [
            s for s in xml.find_all("dim:field", element="subject") if s.string
        ]:
            if not subject.get("qualifier"):
                subjects_dict.setdefault("Subject scheme not provided", []).append(
                    subject.string
                )
            else:
                subjects_dict.setdefault(subject["qualifier"], []).append(
                    subject.string
                )
        for key, value in subjects_dict.items():
            fields.setdefault("subjects", []).append(
                timdex.Subject(value=value, kind=key)
            )

        # summary, uses description list retrieved for notes field
        for description in [
            d for d in descriptions if d.get("qualifier") == "abstract" and d.string
        ]:
            fields.setdefault("summary", []).append(description.string)

        return fields

    @classmethod
    def get_content_types(cls, xml: Tag) -> Optional[list[str]]:
        """
        Retrieve content types from a DSpace DIM XML record.

        May be overridden by source subclasses that retrieve content type values
        differently.

        Args:
            xml: A BeautifulSoup Tag representing a single DSpace DIM XML record.
        """
        return [
            t.string for t in xml.find_all("dim:field", element="type", string=True)
        ] or None

    @classmethod
    def get_main_titles(cls, xml: Tag) -> list[Tag]:
        """
        Retrieve main title(s) from a DSpace DIM XML record.

        Overrides metaclass get_main_titles() method.

        Args:
            xml: A BeautifulSoup Tag representing a single DSpace DIM XML record.
        """
        return [
            t
            for t in xml.find_all("dim:field", element="title")
            if "qualifier" not in t.attrs
        ]

    @classmethod
    def get_source_record_id(cls, xml: Tag) -> str:
        """
        Get the source record ID from a DSpace DIM XML record.

        Overrides metaclass get_source_record_id() method.

        Args:
            xml: A BeautifulSoup Tag representing a single DSpace DIM XML record.
        """
        return xml.header.identifier.string.split(":")[2]

    @classmethod
    def valid_content_types(cls, content_type_list: List[str]) -> bool:
        """
        Validate a list of content_type values from a DSpace DIM XML record.

        May be overridden by source subclasses that require content type validation.

        Args:
            content_type_list: A list of content_type values.
        """
        return True
