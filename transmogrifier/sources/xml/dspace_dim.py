import logging
from collections.abc import Iterator

from bs4 import Tag  # type: ignore[import-untyped]

import transmogrifier.models as timdex
from transmogrifier.helpers import validate_date, validate_date_range
from transmogrifier.sources.xmltransformer import XMLTransformer

logger = logging.getLogger(__name__)


class DspaceDim(XMLTransformer):
    """DSpace DIM transformer."""

    def get_optional_fields(self, source_record: Tag) -> dict | None:
        """
        Retrieve optional TIMDEX fields from a DSpace DIM XML record.

        Overrides metaclass get_optional_fields() method.

        Args:
            source_record: A BeautifulSoup Tag representing a single DSpace DIM XML
            record.
        """
        fields: dict = {}

        source_record_id = self.get_source_record_id(source_record)

        # alternate_titles
        for alternate_title in [
            t
            for t in source_record.find_all("dim:field", element="title")
            if "qualifier" in t.attrs and t.string
        ]:
            fields.setdefault("alternate_titles", []).append(
                timdex.AlternateTitle(
                    value=alternate_title.string,
                    kind=alternate_title["qualifier"] or None,
                )
            )
        # If the record has more than one main title, add extras to alternate_titles
        for index, title in enumerate(self.get_main_titles(source_record)):
            if index > 0:
                fields.setdefault("alternate_titles", []).append(
                    timdex.AlternateTitle(value=title)
                )

        # citation
        citation = source_record.find(
            "dim:field", element="identifier", qualifier="citation"
        )
        fields["citation"] = citation.string if citation and citation.string else None

        # content_type
        if content_types := self.get_content_types(source_record):
            if self.valid_content_types(content_types):
                fields["content_type"] = content_types
            else:
                return None

        # contents
        fields["contents"] = self.get_contents(source_record) or None

        # contributors
        for creator in [
            c for c in source_record.find_all("dim:field", element="creator") if c.string
        ]:
            fields.setdefault("contributors", []).append(
                timdex.Contributor(
                    value=creator.string,
                    kind="Creator",
                )
            )

        for contributor in [
            c
            for c in source_record.find_all("dim:field", element="contributor")
            if c.string
        ]:
            fields.setdefault("contributors", []).append(
                timdex.Contributor(
                    value=contributor.string,
                    kind=contributor.get("qualifier") or "Not specified",
                )
            )

        # dates
        fields["dates"] = self.get_dates(source_record, source_record_id) or None

        # file_formats
        fields["file_formats"] = [
            f.string
            for f in source_record.find_all("dim:field", element="format")
            if f.get("qualifier") == "mimetype" and f.string
        ] or None

        # format
        fields["format"] = "electronic resource"

        # funding_information
        for funding_reference in [
            f
            for f in source_record.find_all(
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
        identifiers = source_record.find_all("dim:field", element="identifier")
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
            for la in source_record.find_all("dim:field", element="language")
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
            for lo in source_record.find_all(
                "dim:field", element="coverage", qualifier="spatial"
            )
            if lo.string
        ] or None

        # notes
        descriptions = source_record.find_all("dim:field", element="description")
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

        # publishers
        fields["publishers"] = [
            timdex.Publisher(name=p.string)
            for p in source_record.find_all("dim:field", element="publisher")
            if p.string
        ] or None

        # related_items
        for related_item in [
            r for r in source_record.find_all("dim:field", element="relation") if r.string
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
            r for r in source_record.find_all("dim:field", element="rights") if r.string
        ]:
            if rights.get("qualifier") == "uri":
                rg = timdex.Rights(uri=rights.string)
            else:
                rg = timdex.Rights(
                    description=rights.string, kind=rights.get("qualifier") or None
                )
            fields.setdefault("rights", []).append(rg)

        # subjects
        subjects_dict: dict[str, list[str]] = {}
        for subject in [
            s for s in source_record.find_all("dim:field", element="subject") if s.string
        ]:
            if not subject.get("qualifier"):
                subjects_dict.setdefault("Subject scheme not provided", []).append(
                    subject.string
                )
            else:
                subjects_dict.setdefault(subject["qualifier"], []).append(subject.string)
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
    def get_contents(cls, source_record: Tag) -> list[str]:
        return [
            str(contents.string)
            for contents in source_record.find_all(
                "dim:field",
                element="description",
                qualifier="tableofcontents",
                string=True,
            )
        ]

    @classmethod
    def get_dates(cls, source_record: Tag, source_record_id: str) -> list[timdex.Date]:
        dates = []
        dates.extend(list(cls._parse_date_elements(source_record, source_record_id)))
        dates.extend(list(cls._parse_coverage_elements(source_record, source_record_id)))
        return dates

    @classmethod
    def _parse_date_elements(
        cls, source_record: Tag, source_record_id: str
    ) -> Iterator[timdex.Date]:
        for date_element in source_record.find_all(
            "dim:field", element="date", string=True
        ):
            date_value = str(date_element.string.strip())
            if validate_date(date_value, source_record_id):
                if date_element.get("qualifier") == "issued":
                    date_object = timdex.Date(value=date_value, kind="Publication date")
                else:
                    date_object = timdex.Date(
                        value=date_value, kind=date_element.get("qualifier") or None
                    )
                yield date_object

    @classmethod
    def _parse_coverage_elements(
        cls, source_record: Tag, source_record_id: str
    ) -> Iterator[timdex.Date]:
        for coverage_value in [
            str(coverage_element.string)
            for coverage_element in source_record.find_all(
                "dim:field", element="coverage", qualifier="temporal", string=True
            )
        ]:
            if "/" in coverage_value:
                date_object = cls._parse_date_range(coverage_value, source_record_id)
            else:
                date_object = timdex.Date(note=coverage_value, kind="coverage")
            if date_object:
                yield date_object

    @classmethod
    def _parse_date_range(
        cls, coverage_value: Tag, source_record_id: str
    ) -> timdex.Date | None:
        """Parse date range value and return a Date object if it is validated."""
        split = coverage_value.index("/")
        gte_date = coverage_value[:split]
        lte_date = coverage_value[split + 1 :]
        if validate_date_range(
            gte_date,
            lte_date,
            source_record_id,
        ):
            return timdex.Date(
                range=timdex.DateRange(
                    gte=gte_date,
                    lte=lte_date,
                ),
                kind="coverage",
            )
        return None

    @classmethod
    def get_content_types(cls, source_record: Tag) -> list[str] | None:
        """
        Retrieve content types from a DSpace DIM XML record.

        May be overridden by source subclasses that retrieve content type values
        differently.

        Args:
            source_record: A BeautifulSoup Tag representing a single DSpace DIM XML
            record.
        """
        return [
            t.string
            for t in source_record.find_all("dim:field", element="type", string=True)
        ] or None

    @classmethod
    def get_main_titles(cls, source_record: Tag) -> list[str]:
        """
        Retrieve main title(s) from a DSpace DIM XML record.

        Overrides metaclass get_main_titles() method.

        Args:
            source_record: A BeautifulSoup Tag representing a single DSpace DIM XML
            record.
        """
        return [
            t.string
            for t in source_record.find_all("dim:field", element="title", string=True)
            if "qualifier" not in t.attrs
        ]

    @classmethod
    def get_source_record_id(cls, source_record: Tag) -> str:
        """
        Get the source record ID from a DSpace DIM XML record.

        Overrides metaclass get_source_record_id() method.

        Args:
            source_record: A BeautifulSoup Tag representing a single DSpace DIM XML
            record.
        """
        return source_record.header.identifier.string.split(":")[2]

    @classmethod
    def valid_content_types(cls, _content_type_list: list[str]) -> bool:
        """
        Validate a list of content_type values from a DSpace DIM XML record.

        May be overridden by source subclasses that require content type validation.

        Args:
            content_type_list: A list of content_type values.
        """
        return True
