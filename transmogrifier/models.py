import functools
import logging
from collections.abc import Callable
from enum import StrEnum
from typing import Any, Self

import attrs
from attrs import asdict, define, field, validators
from attrs.validators import instance_of, optional

logger = logging.getLogger(__name__)


def check_range(
    _instance: "Date", attribute: "attrs.Attribute", value: "DateRange"
) -> None:
    if value is None:
        return
    if value.gt and value.gte:
        message = (
            f"{attribute.name} may have a 'gt' or 'gte' value, but not both; "
            f"received {value}"
        )
        raise ValueError(message)
    if value.lt and value.lte:
        message = (
            f"{attribute.name} may have a 'lt' or 'lte' value, but not both; "
            f"received {value}"
        )
        raise ValueError(message)


def list_of(item_type: Any) -> Callable:  # noqa: ANN401
    return validators.and_(
        validators.deep_iterable(
            member_validator=instance_of(item_type),
            iterable_validator=instance_of(list),
        ),
        not_empty,
    )


def not_empty(
    _instance: "TimdexRecord", attribute: "attrs.Attribute", value: "list"
) -> None:
    if len(value) == 0:
        message = f"'{attribute.name}' cannot be an empty list, received: '{value}'."
        raise ValueError(message)


def timdex_object_hash(timdex_object: Any) -> int:  # noqa: ANN401
    """Hash method for TIMDEX objects.

    This method is set as the hash method for TIMDEX objects.
    The method generates a unique hash using a tuple
    comprised of the class name and attribute values.
    By making TIMDEX objects hashable, dedupe methods
    can be applied to a list of TIMDEX objects.
    """
    values = (timdex_object.__class__.__name__,)
    values += tuple(
        [
            tuple(attrib) if isinstance(attrib, list) else attrib
            for attrib in attrs.astuple(timdex_object)
        ]
    )
    return hash(values)


def dedupe(item_list: list | Any) -> list | None:  # noqa: ANN401
    """Deduplication method for list of items.

    This method is used as a converter function for list fields
    in the TimdexRecord model.
    """
    if not isinstance(item_list, list):
        return item_list
    return list(dict.fromkeys(item_list))


class ControlledValue(StrEnum):
    """Base class for controlled vocabularies of TIMDEX field values.

    Subclasses define members (the controlled values) and a default(), and may
    define mappings() for source values that should map to a member.

    Constructing a member directly, e.g. IdentifierKind("DOI"), is strict and raises
    a ValueError for anything but an exact controlled value.  from_raw() is the
    lenient path for raw source values, and is intended as an attrs converter.
    """

    @classmethod
    def mappings(cls) -> dict[str, Self]:
        """Map source values to members, in addition to the members themselves.

        Keys are matched case-insensitively, like member values.  A mapping to
        default() records a known source value without logging it as unmapped.
        """
        return {}

    @classmethod
    def default(cls) -> Self:
        """Member returned for None or unmapped source values."""
        message = f"{cls.__name__} must define a default()"
        raise NotImplementedError(message)

    @classmethod
    @functools.cache
    def from_raw(cls, value: str | None) -> Self:
        """Map a raw source value to a member, never raising.

        Every member maps to itself (case-insensitive, whitespace stripped), plus any
        mappings().  None and unmapped values return default(), with unmapped values
        logged.  Results are cached per input value, so the mapping is only built on
        a cache miss and each unmapped value is only logged once.
        """
        if value is None:
            return cls.default()
        try:
            return cls.all_mappings()[value.strip().lower()]
        except KeyError:
            logger.warning(
                f"{cls.__name__} value '{value}' could not be mapped, "
                f"defaulting to '{cls.default()}'.  This warning will only be "
                "logged once per run, not per instance encountered."
            )
            return cls.default()

    @classmethod
    def all_mappings(cls) -> dict[str, Self]:
        """All source values that map to a member, as matched by from_raw().

        Every member maps to itself, plus any mappings(), with keys lowercased.  Useful
        for seeing the full set of source values a vocabulary accepts.
        """
        return {member.lower(): member for member in cls} | {
            raw.lower(): member for raw, member in cls.mappings().items()
        }


@define
class AlternateTitle:
    value: str = field(validator=instance_of(str))  # Required subfield
    kind: str | None = field(default=None, validator=optional(instance_of(str)))

    __hash__ = timdex_object_hash


@define
class Contributor:
    value: str = field(validator=instance_of(str))  # Required subfield
    affiliation: list[str] | None = field(default=None, validator=optional(list_of(str)))
    identifier: list[str] | None = field(default=None, validator=optional(list_of(str)))
    kind: str | None = field(default=None, validator=optional(instance_of(str)))
    mit_affiliated: bool | None = field(
        default=None, validator=optional(instance_of(bool))
    )

    __hash__ = timdex_object_hash


@define
class DateRange:
    gt: str | None = field(default=None, validator=optional(instance_of(str)))
    gte: str | None = field(default=None, validator=optional(instance_of(str)))
    lt: str | None = field(default=None, validator=optional(instance_of(str)))
    lte: str | None = field(default=None, validator=optional(instance_of(str)))


@define
class Date:
    kind: str | None = field(default=None, validator=optional(instance_of(str)))
    note: str | None = field(default=None, validator=optional(instance_of(str)))
    range: DateRange | None = field(  # type: ignore[misc]
        default=None,
        validator=[optional(instance_of(DateRange)), check_range],
    )
    value: str | None = field(default=None, validator=optional(instance_of(str)))

    __hash__ = timdex_object_hash


@define
class Funder:
    funder_name: str | None = field(default=None, validator=optional(instance_of(str)))
    funder_identifier: str | None = field(
        default=None, validator=optional(instance_of(str))
    )
    funder_identifier_type: str | None = field(
        default=None, validator=optional(instance_of(str))
    )
    award_number: str | None = field(default=None, validator=optional(instance_of(str)))
    award_uri: str | None = field(default=None, validator=optional(instance_of(str)))

    __hash__ = timdex_object_hash


@define
class Holding:
    call_number: str | None = field(default=None, validator=optional(instance_of(str)))
    collection: str | None = field(default=None, validator=optional(instance_of(str)))
    format: str | None = field(default=None, validator=optional(instance_of(str)))
    location: str | None = field(default=None, validator=optional(instance_of(str)))
    note: str | None = field(default=None, validator=optional(instance_of(str)))

    __hash__ = timdex_object_hash


@define
class Identifier:
    class IdentifierKind(ControlledValue):
        """Controlled values for Identifier.kind."""

        ALEPH = "Aleph"
        COLLECTION_IDENTIFIER = "Collection Identifier"
        DOI = "DOI"
        GOVDOC = "GovDoc"
        ISBN = "ISBN"
        ISMN = "ISMN"
        ISSN = "ISSN"
        LCCN = "LCCN"
        LIBGUIDE_ID = "LibGuide ID"
        NOT_SPECIFIED = "Not Specified"
        OAI_PMH = "OAI-PMH"
        OCLC = "OCLC"
        ORCID = "ORCID"
        PMID = "PMID"
        URI = "URI"

        @classmethod
        def mappings(cls) -> dict[str, Self]:
            return {
                "not spec": cls.NOT_SPECIFIED,
                "oclc number": cls.OCLC,
                "other": cls.NOT_SPECIFIED,
                "other identifier": cls.NOT_SPECIFIED,
                "url": cls.URI,
            }

        @classmethod
        def default(cls) -> Self:
            return cls.NOT_SPECIFIED

    value: str = field(validator=instance_of(str))  # Required subfield
    kind: IdentifierKind = field(
        default=IdentifierKind.default(),
        converter=IdentifierKind.from_raw,  # type: ignore[misc]
        validator=instance_of(IdentifierKind),
    )

    __hash__ = timdex_object_hash


@define
class Link:
    url: str = field(validator=instance_of(str))  # Required subfield
    kind: str | None = field(default=None, validator=optional(instance_of(str)))
    restrictions: str | None = field(default=None, validator=optional(instance_of(str)))
    text: str | None = field(default=None, validator=optional(instance_of(str)))

    __hash__ = timdex_object_hash


@define
class Location:
    value: str | None = field(default=None, validator=optional(instance_of(str)))
    kind: str | None = field(default=None, validator=optional(instance_of(str)))
    geoshape: str | None = field(default=None, validator=optional(instance_of(str)))

    __hash__ = timdex_object_hash


@define
class Note:
    value: list[str] = field(validator=list_of(str))  # Required subfield
    kind: str | None = field(default=None, validator=optional(instance_of(str)))

    __hash__ = timdex_object_hash


@define
class Publisher:
    name: str | None = field(default=None, validator=optional(instance_of(str)))
    date: str | None = field(default=None, validator=optional(instance_of(str)))
    location: str | None = field(default=None, validator=optional(instance_of(str)))

    __hash__ = timdex_object_hash


@define
class RelatedItem:
    description: str | None = field(default=None, validator=optional(instance_of(str)))
    item_type: str | None = field(default=None, validator=optional(instance_of(str)))
    relationship: str | None = field(default=None, validator=optional(instance_of(str)))
    uri: str | None = field(default=None, validator=optional(instance_of(str)))

    __hash__ = timdex_object_hash


@define
class Rights:
    description: str | None = field(default=None, validator=optional(instance_of(str)))
    kind: str | None = field(default=None, validator=optional(instance_of(str)))
    uri: str | None = field(default=None, validator=optional(instance_of(str)))

    __hash__ = timdex_object_hash


@define
class Subject:
    value: list[str] = field(validator=list_of(str))  # Required subfield
    kind: str | None = field(default=None, validator=optional(instance_of(str)))

    __hash__ = timdex_object_hash


@define
class TimdexProvenance:
    source: str = field(default=None, validator=instance_of(str))
    run_date: str = field(default=None, validator=instance_of(str))
    run_id: str = field(default=None, validator=instance_of(str))
    run_record_offset: int = field(default=None, validator=instance_of(int))

    __hash__ = timdex_object_hash


@define
class TimdexRecord:
    # Required fields
    source: str = field(validator=instance_of(str))
    source_link: str = field(validator=instance_of(str))
    timdex_record_id: str = field(validator=instance_of(str))
    title: str = field(validator=instance_of(str))

    # Optional fields
    alternate_titles: list[AlternateTitle] | None = field(
        default=None, converter=dedupe, validator=optional(list_of(AlternateTitle))
    )
    call_numbers: list[str] | None = field(
        default=None, converter=dedupe, validator=optional(list_of(str))
    )
    citation: str | None = field(default=None, validator=optional(instance_of(str)))
    content_type: list[str] | None = field(
        default=None, converter=dedupe, validator=optional(list_of(str))
    )
    contents: list[str] | None = field(
        default=None, converter=dedupe, validator=optional(list_of(str))
    )
    contributors: list[Contributor] | None = field(
        default=None, converter=dedupe, validator=optional(list_of(Contributor))
    )
    dates: list[Date] | None = field(
        default=None, converter=dedupe, validator=optional(list_of(Date))
    )
    edition: str | None = field(default=None, validator=optional(instance_of(str)))
    file_formats: list[str] | None = field(
        default=None, converter=dedupe, validator=optional(list_of(str))
    )
    format: str | None = field(default=None, validator=optional(instance_of(str)))
    fulltext: str | None = field(default=None, validator=optional(instance_of(str)))
    funding_information: list[Funder] | None = field(
        default=None, converter=dedupe, validator=optional(list_of(Funder))
    )
    holdings: list[Holding] | None = field(
        default=None, converter=dedupe, validator=optional(list_of(Holding))
    )
    identifiers: list[Identifier] | None = field(
        default=None, converter=dedupe, validator=optional(list_of(Identifier))
    )
    languages: list[str] | None = field(
        default=None, converter=dedupe, validator=optional(list_of(str))
    )
    links: list[Link] | None = field(
        default=None, converter=dedupe, validator=optional(list_of(Link))
    )
    literary_form: str | None = field(default=None, validator=optional(instance_of(str)))
    locations: list[Location] | None = field(
        default=None, converter=dedupe, validator=optional(list_of(Location))
    )
    notes: list[Note] | None = field(
        default=None, converter=dedupe, validator=optional(list_of(Note))
    )
    numbering: str | None = field(default=None, validator=optional(instance_of(str)))
    physical_description: str | None = field(
        default=None, validator=optional(instance_of(str))
    )
    provider: str | None = field(default=None, validator=optional(instance_of(str)))
    publication_frequency: list[str] | None = field(
        default=None, converter=dedupe, validator=optional(list_of(str))
    )
    publishers: list[Publisher] | None = field(
        default=None, converter=dedupe, validator=optional(list_of(Publisher))
    )
    related_items: list[RelatedItem] | None = field(
        default=None, converter=dedupe, validator=optional(list_of(RelatedItem))
    )
    rights: list[Rights] | None = field(
        default=None, converter=dedupe, validator=optional(list_of(Rights))
    )
    subjects: list[Subject] | None = field(
        default=None, converter=dedupe, validator=optional(list_of(Subject))
    )
    summary: list[str] | None = field(
        default=None, converter=dedupe, validator=optional(list_of(str))
    )
    timdex_provenance: TimdexProvenance | None = field(
        default=None, validator=optional(instance_of(TimdexProvenance))
    )

    def asdict(self) -> dict[str, Any]:
        return asdict(self, filter=lambda _, value: value is not None)

    @classmethod
    def get_required_field_names(cls) -> list[str]:
        return [
            field
            for field, attribute in attrs.fields_dict(cls).items()
            if attribute.default is attrs.NOTHING
        ]

    @classmethod
    def get_optional_field_names(cls) -> list[str]:
        return [
            field
            for field, attribute in attrs.fields_dict(cls).items()
            if attribute.default is None
        ]
