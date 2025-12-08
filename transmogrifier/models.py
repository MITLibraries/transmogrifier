from collections.abc import Callable
from typing import Any

import attrs
from attrs import asdict, define, field, validators
from attrs.validators import instance_of, optional


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
    value: str = field(validator=instance_of(str))  # Required subfield
    kind: str | None = field(default=None, validator=optional(instance_of(str)))

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
