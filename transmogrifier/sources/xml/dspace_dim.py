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

        # alternate_titles
        fields["alternate_titles"] = self.get_alternate_titles(source_record)

        # citation
        fields["citation"] = self.get_citation(source_record)

        # content_type
        fields["content_type"] = self.get_content_type(source_record)

        # contents
        fields["contents"] = self.get_contents(source_record)

        # contributors
        fields["contributors"] = self.get_contributors(source_record)

        # dates
        fields["dates"] = self.get_dates(source_record)

        # file_formats
        fields["file_formats"] = self.get_file_formats(source_record)

        # format
        fields["format"] = self.get_format()

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
    def get_alternate_titles(
        cls, source_record: Tag
    ) -> list[timdex.AlternateTitle] | None:
        alternate_titles = [
            timdex.AlternateTitle(
                value=str(alternate_title.string),
                kind=alternate_title["qualifier"],
            )
            for alternate_title in source_record.find_all(
                "dim:field", element="title", string=True
            )
            if alternate_title.get("qualifier")
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
            "dim:field", element="identifier", qualifier="citation", string=True
        ):
            return citation.string
        return None

    @classmethod
    def get_content_type(cls, source_record: Tag) -> list[str] | None:
        return [
            str(content_type.string)
            for content_type in source_record.find_all(
                "dim:field", element="type", string=True
            )
        ] or None

    @classmethod
    def get_contents(cls, source_record: Tag) -> list[str] | None:
        return [
            contents.string
            for contents in source_record.find_all(
                "dim:field",
                element="description",
                qualifier="tableofcontents",
                string=True,
            )
        ] or None

    @classmethod
    def get_contributors(cls, source_record: Tag) -> list[timdex.Contributor] | None:
        contributors = []
        contributors.extend(list(cls._get_creators(source_record)))
        contributors.extend(
            list(cls._get_contributors_by_contributor_element(source_record))
        )
        return contributors or None

    @classmethod
    def _get_creators(cls, source_record: Tag) -> Iterator[timdex.Contributor]:
        for creator in source_record.find_all(
            "dim:field", element="creator", string=True
        ):
            yield timdex.Contributor(
                value=str(creator.string),
                kind="Creator",
            )

    @classmethod
    def _get_contributors_by_contributor_element(
        cls, source_record: Tag
    ) -> Iterator[timdex.Contributor]:
        for contributor in source_record.find_all(
            "dim:field", element="contributor", string=True
        ):
            yield timdex.Contributor(
                value=str(contributor.string),
                kind=contributor.get("qualifier") or "Not specified",
            )

    @classmethod
    def get_dates(cls, source_record: Tag) -> list[timdex.Date] | None:
        dates = []
        for date in source_record.find_all("dim:field", element="date", string=True):
            date_value = str(date.string.strip())
            if validate_date(date_value, cls.get_source_record_id(source_record)):
                if date.get("qualifier") == "issued":
                    date_object = timdex.Date(value=date_value, kind="Publication date")
                else:
                    date_object = timdex.Date(
                        value=date_value, kind=date.get("qualifier") or None
                    )
                dates.append(date_object)
        dates.extend(list(cls._get_coverage_dates(source_record)))
        return dates or None

    @classmethod
    def _get_coverage_dates(cls, source_record: Tag) -> Iterator[timdex.Date]:
        for coverage_value in [
            str(coverage.string)
            for coverage in source_record.find_all(
                "dim:field", element="coverage", qualifier="temporal", string=True
            )
        ]:
            if "/" in coverage_value:
                split = coverage_value.index("/")
                gte_date = coverage_value[:split]
                lte_date = coverage_value[split + 1 :]
                if validate_date_range(
                    gte_date,
                    lte_date,
                    cls.get_source_record_id(source_record),
                ):
                    yield timdex.Date(
                        range=timdex.DateRange(
                            gte=gte_date,
                            lte=lte_date,
                        ),
                        kind="coverage",
                    )
            else:
                yield timdex.Date(note=coverage_value, kind="coverage")

    @classmethod
    def get_file_formats(cls, source_record: Tag) -> list[str] | None:
        return [
            str(file_format.string)
            for file_format in source_record.find_all(
                "dim:field", element="format", string=True
            )
            if file_format.get("qualifier") == "mimetype"
        ] or None

    @classmethod
    def get_format(cls) -> str:
        return "electronic resource"

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
