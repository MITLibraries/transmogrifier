import logging
from typing import Dict, Iterator, List

from bs4 import Tag

from transmogrifier.models import (
    AlternateTitle,
    Contributor,
    Date,
    Funder,
    Identifier,
    Note,
    RelatedItem,
    Rights,
    Subject,
    TimdexRecord,
)

logger = logging.getLogger(__name__)


class DSpaceDim:
    def __init__(
        self,
        source: str,
        source_base_url: str,
        source_name: str,
        input_records: Iterator[Tag],
    ) -> None:
        self.source = source
        self.source_base_url = source_base_url
        self.source_name = source_name
        self.input_records = input_records

    def __iter__(self) -> Iterator[TimdexRecord]:
        return self

    def __next__(self) -> TimdexRecord:
        xml = next(self.input_records)
        record = self.create_from_dspace_dim(
            self.source, self.source_base_url, self.source_name, xml
        )
        return record

    @classmethod
    def create_from_dspace_dim(
        cls, source: str, source_base_url: str, source_name: str, xml: Tag
    ) -> TimdexRecord:
        """
        Args:
            source: A label for the source repository that is prepended to the
            timdex_record_id.
            source_base_url: The base URL for the source system from which direct links
            to source metadata records can be constructed.
            source_name: The full human-readable name of the source repository to be
            used in the TIMDEX record.
            xml: A BeautifulSoup Tag representing a single DSpace record in
            dim XML.
        """
        # Required fields in TIMDEX
        source_record_id = xml.header.find("identifier").string
        all_titles = xml.find_all("dim:field", element="title")
        main_title = [t for t in all_titles if "qualifier" not in t.attrs]
        if len(main_title) != 1:
            raise ValueError(
                "A record must have exactly one title. Titles found for record "
                f"{source_record_id}: {main_title}"
            )
        kwargs = {
            "source": source_name,
            "source_link": source_base_url + source_record_id,
            "timdex_record_id": f"{source}:{source_record_id.replace('/', '-')}",
            "title": main_title[0].string,
        }

        # Optional fields in TIMDEX
        # alternate_titles, uses full title list retrieved for main title field
        for alternate_title in [
            t for t in all_titles if "qualifier" in t.attrs and t.string
        ]:
            a = AlternateTitle(
                value=alternate_title.string,
                kind=alternate_title.get("qualifier"),
            )
            kwargs.setdefault("alternate_titles", []).append(a)

        # contributors
        citation_creators = []
        for creator in [
            c for c in xml.find_all("dim:field", element="creator") if c.string
        ]:
            citation_creators.append(creator.string)
            c = Contributor(
                value=creator.string,
                kind="Creator",
            )
            kwargs.setdefault("contributors", []).append(c)

        for contributor in [
            c for c in xml.find_all("dim:field", element="contributor") if c.string
        ]:
            if contributor.get("qualifier") == "author":
                citation_creators.append(contributor.string)
            c = Contributor(value=contributor.string, kind=contributor.get("qualifier"))
            kwargs.setdefault("contributors", []).append(c)

        # dates
        date_issued = ""
        for date in [d for d in xml.find_all("dim:field", element="date") if d.string]:
            d = Date(value=date.string, kind=date.get("qualifier"))
            if date.get("qualifier") == "issued":
                date_issued = date.string
            kwargs.setdefault("dates", []).append(d)

        # file_formats
        for file_format in [
            f
            for f in xml.find_all("dim:field", element="format")
            if "qualifier" in f.attrs
            and f.attrs["qualifier"] == "mimetype"
            and f.string
        ]:
            kwargs.setdefault("file_formats", []).append(file_format.string)

        # format
        kwargs["format"] = "electronic resource"

        # funding_information
        for funding_reference in [
            f
            for f in xml.find_all("dim:field", element="description")
            if "qualifier" in f.attrs
            and f.attrs["qualifier"] == "sponsorship"
            and f.string
        ]:
            fr = Funder(
                funder_name=funding_reference.string,
            )
            kwargs.setdefault("funding_information", []).append(fr)

        # identifiers
        identifiers = xml.find_all("dim:field", element="identifier")
        for identifier in [
            i for i in identifiers if i.get("qualifier") != "citation" and i.string
        ]:
            i = Identifier(
                value=identifier.string,
                kind=identifier.get("qualifier"),
            )
            kwargs.setdefault("identifiers", []).append(i)

        # language
        for language in [
            la for la in xml.find_all("dim:field", element="language") if la.string
        ]:
            kwargs.setdefault("languages", []).append(language.string)

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
            ]
            and d.string
        ]:
            n = Note(value=[description.string], kind=description.get("qualifier"))
            kwargs.setdefault("notes", []).append(n)

        # publication_information
        for publisher in [
            p for p in xml.find_all("dim:field", element="publisher") if p.string
        ]:
            kwargs.setdefault("publication_information", []).append(publisher.string)

        # related_items, uses related_identifiers retrieved for identifiers
        for related_item in [
            r for r in xml.find_all("dim:field", element="relation") if r.string
        ]:
            if related_item.get("qualifier") == "uri":
                ri = RelatedItem(uri=related_item.string)
            else:
                ri = RelatedItem(
                    description=related_item.string,
                    relationship=related_item.get("qualifier"),
                )
            kwargs.setdefault("related_items", []).append(ri)

        # rights
        for rights in [
            r for r in xml.find_all("dim:field", element="rights") if r.string
        ]:
            if rights.get("qualifier") == "uri":
                rg = Rights(uri=rights.string)
            else:
                rg = Rights(description=rights.string, kind=rights.get("qualifier"))
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
                subjects_dict.setdefault(subject.attrs["qualifier"], []).append(
                    subject.string
                )
        for key, value in subjects_dict.items():
            s = Subject(value=value, kind=key)
            kwargs.setdefault("subjects", []).append(s)

        # summary, uses description list retrieved for notes field
        for description in [
            d for d in descriptions if d.get("qualifier") == "abstract" and d.string
        ]:
            kwargs.setdefault("summary", []).append(description.string)

        # citation, uses identifiers list retrieved for identifiers field
        citation = ""
        for identifier in [
            i for i in identifiers if i.get("qualifier") == "citation" and i.string
        ]:
            citation = identifier.string
        if citation == "":
            if citation_creators:
                citation += f"{'; '.join(citation_creators)} "
            if date_issued:
                citation += f"({date_issued}): "
            citation += f"{main_title[0].string}. "
            if "publication_information" in kwargs:
                citation += f"{kwargs['publication_information'][0]}. "
            citation += kwargs["source_link"]
        kwargs["citation"] = citation

        return TimdexRecord(**kwargs)
