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
        source_record_id = cls.create_source_record_id(xml)
        all_fields = xml.metadata.find_all("field")
        all_titles = [f for f in all_fields if f.attrs["element"] == "title"]
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
            t
            for t in all_titles
            if "qualifier" in t.attrs and t.attrs["qualifier"] == "alternative"
        ]:
            a = AlternateTitle(
                value=alternate_title.string,
                kind="AlternativeTitle",
            )
            kwargs.setdefault("alternate_titles", []).append(a)

        # contributors
        citation_creators = []
        for creator in [f for f in all_fields if f.attrs["element"] == "creator"]:
            creator_name = creator.string
            citation_creators.append(creator_name)
            c = Contributor(
                value=creator_name,
                kind="Creator",
            )
            kwargs.setdefault("contributors", []).append(c)

        for contributor in [
            f for f in all_fields if f.attrs["element"] == "contributor"
        ]:
            c = Contributor(
                value=contributor.string,
            )
            if "qualifier" in contributor.attrs:
                c.kind = contributor.attrs["qualifier"]
            kwargs.setdefault("contributors", []).append(c)

        # dates
        date_issued = ""
        for date in [f for f in all_fields if f.attrs["element"] == "date"]:
            d = Date(value=date.string)
            if "qualifier" in date.attrs:
                d.kind = date.attrs["qualifier"]
            if date.attrs["qualifier"] == "issued":
                date_issued = date.string
            kwargs.setdefault("dates", []).append(d)

        # file_formats
        for file_format in [
            f
            for f in all_fields
            if f.attrs["element"] == "format"
            and "qualifier" in f.attrs
            and f.attrs["qualifier"] == "mimetype"
        ]:
            kwargs.setdefault("file_formats", []).append(file_format.string)

        # format
        kwargs["format"] = "electronic resource"

        # funding_information
        for funding_reference in [
            f
            for f in all_fields
            if f.attrs["element"] == "description"
            and "qualifier" in f.attrs
            and f.attrs["qualifier"] == "sponsorship"
        ]:
            fr = Funder(
                funder_name=funding_reference.string,
            )
            kwargs.setdefault("funding_information", []).append(fr)

        # identifiers
        identifiers = [f for f in all_fields if f.attrs["element"] == "identifier"]
        for identifier in identifiers:
            if "qualifier" not in identifier.attrs:
                i = Identifier(
                    value=identifier.string,
                )
                kwargs.setdefault("identifiers", []).append(i)
            elif (
                "qualifier" in identifier.attrs
                and identifier.attrs["qualifier"] != "citation"
            ):
                i = Identifier(
                    value=identifier.string,
                    kind=identifier.attrs["qualifier"],
                )
                kwargs.setdefault("identifiers", []).append(i)

        # language
        for language in [
            f
            for f in all_fields
            if f.attrs["element"] == "language"
            and "qualifier" in f.attrs
            and f.attrs["qualifier"] == "iso"
        ]:
            kwargs.setdefault("languages", []).append(language.string)

        # notes
        descriptions = [f for f in all_fields if f.attrs["element"] == "description"]
        for description in descriptions:
            if "qualifier" not in description.attrs:
                n = Note(
                    value=[description.string],
                )
                kwargs.setdefault("notes", []).append(n)
            elif "qualifier" in description.attrs and description.attrs[
                "qualifier"
            ] not in [
                "abstract",
                "provenance",
                "sponsorship",
            ]:
                n = Note(
                    value=[description.string],
                    kind=description.attrs["qualifier"],
                )
                kwargs.setdefault("notes", []).append(n)

        # publication_information
        for publisher in [f for f in all_fields if f.attrs["element"] == "publisher"]:
            kwargs.setdefault("publication_information", []).append(publisher.string)

        # related_items, uses related_identifiers retrieved for identifiers
        for related_item in [f for f in all_fields if f.attrs["element"] == "relation"]:
            if (
                "qualifier" in related_item.attrs
                and related_item.attrs["qualifier"] == "uri"
            ):
                ri = RelatedItem(uri=related_item.string)
            else:
                ri = RelatedItem(description=related_item.string)
                if "qualifier" in related_item.attrs:
                    ri.relationship = related_item.attrs["qualifier"]
            kwargs.setdefault("related_items", []).append(ri)

        # rights
        for rights in [f for f in all_fields if f.attrs["element"] == "rights"]:
            if "qualifier" in rights.attrs and rights.attrs["qualifier"] == "uri":
                rg = Rights(uri=rights.string)
            else:
                rg = Rights(description=rights.string)
                if "qualifier" in rights.attrs:
                    rg.kind = rights.attrs["qualifier"]
            kwargs.setdefault("rights", []).append(rg)

        # subjects
        subjects_dict: Dict[str, List[str]] = {}
        for subject in [f for f in all_fields if f.attrs["element"] == "subject"]:
            if "qualifier" not in subject.attrs:
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
            d
            for d in descriptions
            if "qualifier" in d.attrs and d.attrs["qualifier"] == "abstract"
        ]:
            kwargs.setdefault("summary", []).append(description.string)

        # citation, uses identifiers list retrieved for identifiers field
        citation = ""
        for identifier in identifiers:
            if (
                "qualifier" in identifier.attrs
                and identifier.attrs["qualifier"] == "citation"
            ):
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

    @classmethod
    def create_source_record_id(cls, xml: Tag) -> str:
        """
        Create a source record ID from a Datacite XML record.
        Args:
            xml: A BeautifulSoup Tag representing a single DSpace record in
            dim XML.
        """
        source_record_id = xml.header.find("identifier").string
        return source_record_id
