import logging
from collections import defaultdict
from collections.abc import Iterator

from bs4 import Tag  # type: ignore[import-untyped]

import transmogrifier.models as timdex
from transmogrifier.helpers import validate_date, validate_date_range
from transmogrifier.sources.xmltransformer import XMLTransformer

logger = logging.getLogger(__name__)


class DspaceDim(XMLTransformer):
    """DSpace DIM transformer."""

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
        contributors: list[timdex.Contributor] = []
        contributors.extend(cls._get_creators(source_record))
        contributors.extend(cls._get_contributors_by_contributor_element(source_record))
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
        dates.extend(cls._get_coverage_dates(source_record))
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
    def get_format(cls, _source_record: Tag) -> str:
        return "electronic resource"

    @classmethod
    def get_funding_information(cls, source_record: Tag) -> list[timdex.Funder] | None:
        return [
            timdex.Funder(
                funder_name=str(funding_reference.string),
            )
            for funding_reference in source_record.find_all(
                "dim:field", element="description", qualifier="sponsorship", string=True
            )
        ] or None

    @classmethod
    def get_identifiers(cls, source_record: Tag) -> list[timdex.Identifier] | None:
        return [
            timdex.Identifier(
                value=str(identifier.string),
                kind=identifier.get("qualifier") or "Not specified",
            )
            for identifier in source_record.find_all(
                "dim:field", element="identifier", string=True
            )
            if identifier.get("qualifier") != "citation"
        ] or None

    @classmethod
    def get_languages(cls, source_record: Tag) -> list[str] | None:
        return [
            str(language.string)
            for language in source_record.find_all(
                "dim:field", element="language", string=True
            )
        ] or None

    @classmethod
    def get_links(cls, source_record: Tag) -> list[timdex.Link] | None:
        return [
            timdex.Link(
                kind="Digital object URL",
                text="Digital object URL",
                url=str(identifier.string),
            )
            for identifier in source_record.find_all(
                "dim:field", element="identifier", string=True
            )
            if identifier.get("qualifier") == "uri"
        ] or None

    @classmethod
    def get_locations(cls, source_record: Tag) -> list[timdex.Location] | None:
        return [
            timdex.Location(value=str(location.string))
            for location in source_record.find_all(
                "dim:field", element="coverage", qualifier="spatial", string=True
            )
        ] or None

    @classmethod
    def get_notes(cls, source_record: Tag) -> list[timdex.Note] | None:
        return [
            timdex.Note(
                value=[str(description.string)],
                kind=description.get("qualifier") or None,
            )
            for description in source_record.find_all(
                "dim:field", element="description", string=True
            )
            if description.get("qualifier")
            not in [
                "abstract",
                "provenance",
                "sponsorship",
                "tableofcontents",
            ]
        ] or None

    @classmethod
    def get_publishers(cls, source_record: Tag) -> list[timdex.Publisher] | None:
        return [
            timdex.Publisher(name=str(publisher.string))
            for publisher in source_record.find_all(
                "dim:field", element="publisher", string=True
            )
        ] or None

    @classmethod
    def get_related_items(cls, source_record: Tag) -> list[timdex.RelatedItem] | None:
        related_items = []
        for relation in source_record.find_all(
            "dim:field", element="relation", string=True
        ):
            if relation.get("qualifier") == "uri":
                related_item = timdex.RelatedItem(
                    uri=str(relation.string), relationship="Not specified"
                )
            else:
                related_item = timdex.RelatedItem(
                    description=str(relation.string),
                    relationship=relation.get("qualifier") or "Not specified",
                )
            related_items.append(related_item)
        return related_items or None

    @classmethod
    def get_rights(cls, source_record: Tag) -> list[timdex.Rights] | None:
        rights_list = []
        for rights in source_record.find_all("dim:field", element="rights", string=True):
            if rights.get("qualifier") == "uri":
                rights_object = timdex.Rights(uri=str(rights.string))
            else:
                rights_object = timdex.Rights(
                    description=str(rights.string), kind=rights.get("qualifier") or None
                )
            rights_list.append(rights_object)
        return rights_list or None

    @classmethod
    def get_subjects(cls, source_record: Tag) -> list[timdex.Subject] | None:
        subjects_dict = defaultdict(list)
        for subject in source_record.find_all(
            "dim:field", element="subject", string=True
        ):
            subjects_dict[
                subject.get("qualifier") or "Subject scheme not provided"
            ].append(str(subject.string))

        return [
            timdex.Subject(value=subject_value, kind=subject_scheme)
            for subject_scheme, subject_value in subjects_dict.items()
        ] or None

    @classmethod
    def get_summary(cls, source_record: Tag) -> list[str] | None:
        return [
            str(description.string)
            for description in source_record.find_all(
                "dim:field", element="description", string=True
            )
            if description.get("qualifier") == "abstract"
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
