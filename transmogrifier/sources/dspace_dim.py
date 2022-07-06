import logging
from typing import Dict, List

from bs4 import Tag

import transmogrifier.models as timdex
from transmogrifier.helpers import generate_citation
from transmogrifier.sources.transformer import Transformer

logger = logging.getLogger(__name__)


class DspaceDim(Transformer):
    """DSpace DIM transformer class."""

    def transform(self, xml: Tag) -> timdex.TimdexRecord:
        """
        Transform a DSpace DIM XML record to a TIMDEX record.

        Overrides the base Transformer.transform() method.

        Args:
            xml: A BeautifulSoup Tag representing a single DSpace DIM XML record.
        """

        # Required fields in TIMDEX
        source_record_id = xml.header.find("identifier").string.replace(
            "oai:darchive.mblwhoilibrary.org:", ""
        )
        all_titles = xml.find_all("dim:field", element="title")
        main_title = [t for t in all_titles if "qualifier" not in t.attrs]
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
            t for t in all_titles if "qualifier" in t.attrs and t.string
        ]:
            kwargs.setdefault("alternate_titles", []).append(
                timdex.AlternateTitle(
                    value=alternate_title.string,
                    kind=alternate_title["qualifier"],
                )
            )

        # citation
        citation = xml.find("dim:field", element="identifier", qualifier="citation")
        kwargs["citation"] = citation.string if citation and citation.string else None

        # content_type
        kwargs["content_type"] = [
            t.string for t in xml.find_all("dim:field", element="type") if t.string
        ] or None

        # contents
        kwargs["contents"] = [
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
            kwargs.setdefault("contributors", []).append(
                timdex.Contributor(
                    value=creator.string,
                    kind="Creator",
                )
            )

        for contributor in [
            c for c in xml.find_all("dim:field", element="contributor") if c.string
        ]:
            kwargs.setdefault("contributors", []).append(
                timdex.Contributor(
                    value=contributor.string, kind=contributor.get("qualifier")
                )
            )

        # dates
        for date in [d for d in xml.find_all("dim:field", element="date") if d.string]:
            if date.get("qualifier") == "issued":
                d = timdex.Date(value=date.string, kind="Publication date")
            else:
                d = timdex.Date(value=date.string, kind=date.get("qualifier"))
            kwargs.setdefault("dates", []).append(d)

        for coverage in [
            c.string
            for c in xml.find_all("dim:field", element="coverage", qualifier="temporal")
            if c.string
        ]:
            if "/" in coverage:
                d = timdex.Date(
                    range=timdex.Date_Range(
                        gte=coverage.string[: coverage.string.index("/")],
                        lte=coverage.string[coverage.string.index("/") + 1 :],
                    ),
                    kind="coverage",
                )
            else:
                d = timdex.Date(note=coverage.string, kind="coverage")
            kwargs.setdefault("dates", []).append(d)

        # file_formats
        kwargs["file_formats"] = [
            f.string
            for f in xml.find_all("dim:field", element="format")
            if f.get("qualifier") == "mimetype" and f.string
        ] or None

        # format
        kwargs["format"] = "electronic resource"

        # funding_information
        for funding_reference in [
            f
            for f in xml.find_all(
                "dim:field", element="description", qualifier="sponsorship"
            )
            if f.string
        ]:
            kwargs.setdefault("funding_information", []).append(
                timdex.Funder(
                    funder_name=funding_reference.string,
                )
            )

        # identifiers
        identifiers = xml.find_all("dim:field", element="identifier")
        for identifier in [
            i for i in identifiers if i.get("qualifier") != "citation" and i.string
        ]:
            kwargs.setdefault("identifiers", []).append(
                timdex.Identifier(
                    value=identifier.string,
                    kind=identifier.get("qualifier", "Identifier kind not specified"),
                )
            )

        # language
        kwargs["languages"] = [
            la.string
            for la in xml.find_all("dim:field", element="language")
            if la.string
        ] or None

        # links, uses identifiers list retrieved for identifiers field
        kwargs["links"] = [
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
        kwargs["locations"] = [
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
            kwargs.setdefault("notes", []).append(
                timdex.Note(
                    value=[description.string], kind=description.get("qualifier")
                )
            )

        # publication_information
        kwargs["publication_information"] = [
            p.string for p in xml.find_all("dim:field", element="publisher") if p.string
        ] or None

        # related_items
        for related_item in [
            r for r in xml.find_all("dim:field", element="relation") if r.string
        ]:
            if related_item.get("qualifier") == "uri":
                ri = timdex.RelatedItem(uri=related_item.string)
            else:
                ri = timdex.RelatedItem(
                    description=related_item.string,
                    relationship=related_item.get("qualifier"),
                )
            kwargs.setdefault("related_items", []).append(ri)

        # rights
        for rights in [
            r for r in xml.find_all("dim:field", element="rights") if r.string
        ]:
            if rights.get("qualifier") == "uri":
                rg = timdex.Rights(uri=rights.string)
            else:
                rg = timdex.Rights(
                    description=rights.string, kind=rights.get("qualifier")
                )
            kwargs.setdefault("rights", []).append(rg)

        # subjects
        subjects_dict: Dict[str, List[str]] = {}
        for subject in [
            s for s in xml.find_all("dim:field", element="subject") if s.string
        ]:
            if subject.get("qualifier") is None:
                subjects_dict.setdefault("Subject scheme not provided", []).append(
                    subject.string
                )
            else:
                subjects_dict.setdefault(subject["qualifier"], []).append(
                    subject.string
                )
        for key, value in subjects_dict.items():
            kwargs.setdefault("subjects", []).append(
                timdex.Subject(value=value, kind=key)
            )

        # summary, uses description list retrieved for notes field
        for description in [
            d for d in descriptions if d.get("qualifier") == "abstract" and d.string
        ]:
            kwargs.setdefault("summary", []).append(description.string)

        if kwargs.get("citation") is None:
            kwargs["citation"] = generate_citation(kwargs)

        return timdex.TimdexRecord(**kwargs)