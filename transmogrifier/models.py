from typing import Optional

from attrs import asdict, define, field, validators
from attrs.validators import instance_of, optional


def check_range(instance, attribute, value):
    if value is None:
        return
    if value.gt and value.gte:
        raise ValueError(
            f"{attribute.name} may have a 'gt' or 'gte' value, but not both; "
            f"received {value}"
        )
    if value.lt and value.lte:
        raise ValueError(
            f"{attribute.name} may have a 'lt' or 'lte' value, but not both; "
            f"received {value}"
        )


def list_of(item_type):
    return validators.and_(
        validators.deep_iterable(
            member_validator=instance_of(item_type),
            iterable_validator=instance_of(list),
        ),
        not_empty,
    )


def not_empty(instance, attribute, value):
    if len(value) == 0:
        raise ValueError(
            f"'{attribute.name}' cannot be an empty list, received: '{value}'."
        )


@define
class AlternateTitle:
    value: str = field(validator=instance_of(str))  # Required subfield
    kind: Optional[str] = field(default=None, validator=optional(instance_of(str)))


@define
class Contributor:
    value: str = field(validator=instance_of(str))  # Required subfield
    affiliation: Optional[list[str]] = field(
        default=None, validator=optional(list_of(str))
    )
    identifier: Optional[list[str]] = field(
        default=None, validator=optional(list_of(str))
    )
    kind: Optional[str] = field(default=None, validator=optional(instance_of(str)))
    mit_affiliated: Optional[bool] = field(
        default=None, validator=optional(instance_of(bool))
    )


@define
class Date_Range:
    gt: Optional[str] = field(default=None, validator=optional(instance_of(str)))
    gte: Optional[str] = field(default=None, validator=optional(instance_of(str)))
    lt: Optional[str] = field(default=None, validator=optional(instance_of(str)))
    lte: Optional[str] = field(default=None, validator=optional(instance_of(str)))


@define
class Date:
    kind: Optional[str] = field(default=None, validator=optional(instance_of(str)))
    note: Optional[str] = field(default=None, validator=optional(instance_of(str)))
    range: Optional[Date_Range] = field(
        default=None, validator=[optional(instance_of(Date_Range)), check_range]
    )
    value: Optional[str] = field(default=None, validator=optional(instance_of(str)))


@define
class Funder:
    funder_name: Optional[str] = field(
        default=None, validator=optional(instance_of(str))
    )
    funder_identifier: Optional[str] = field(
        default=None, validator=optional(instance_of(str))
    )
    funder_identifier_type: Optional[str] = field(
        default=None, validator=optional(instance_of(str))
    )
    award_number: Optional[str] = field(
        default=None, validator=optional(instance_of(str))
    )
    award_uri: Optional[str] = field(default=None, validator=optional(instance_of(str)))


@define
class Holding:
    call_number: Optional[str] = field(
        default=None, validator=optional(instance_of(str))
    )
    collection: Optional[str] = field(
        default=None, validator=optional(instance_of(str))
    )
    format: Optional[str] = field(default=None, validator=optional(instance_of(str)))
    location: Optional[str] = field(default=None, validator=optional(instance_of(str)))
    note: Optional[str] = field(default=None, validator=optional(instance_of(str)))


@define
class Identifier:
    value: str = field(validator=instance_of(str))  # Required subfield
    kind: Optional[str] = field(default=None, validator=optional(instance_of(str)))


@define
class Link:
    url: str = field(validator=instance_of(str))  # Required subfield
    kind: Optional[str] = field(default=None, validator=optional(instance_of(str)))
    restrictions: Optional[str] = field(
        default=None, validator=optional(instance_of(str))
    )
    text: Optional[str] = field(default=None, validator=optional(instance_of(str)))


@define
class Location:
    value: Optional[str] = field(validator=optional(instance_of(str)))
    kind: Optional[str] = field(default=None, validator=optional(instance_of(str)))
    geodata: Optional[list[float]] = field(
        default=None, validator=optional(list_of(float))
    )


@define
class Note:
    value: list[str] = field(validator=list_of(str))  # Required subfield
    kind: Optional[str] = field(default=None, validator=optional(instance_of(str)))


@define
class RelatedItem:
    description: Optional[str] = field(
        default=None, validator=optional(instance_of(str))
    )
    item_type: Optional[str] = field(default=None, validator=optional(instance_of(str)))
    relationship: Optional[str] = field(
        default=None, validator=optional(instance_of(str))
    )
    uri: Optional[str] = field(default=None, validator=optional(instance_of(str)))


@define
class Rights:
    description: Optional[str] = field(
        default=None, validator=optional(instance_of(str))
    )
    kind: Optional[str] = field(default=None, validator=optional(instance_of(str)))
    uri: Optional[str] = field(default=None, validator=optional(instance_of(str)))


@define
class Subject:
    value: list[str] = field(validator=list_of(str))  # Required subfield
    kind: Optional[str] = field(default=None, validator=optional(instance_of(str)))


@define
class TimdexRecord:
    # Required fields
    source: str = field(validator=instance_of(str))
    source_link: str = field(validator=instance_of(str))
    timdex_record_id: str = field(validator=instance_of(str))
    title: str = field(validator=instance_of(str))

    # Optional fields
    alternate_titles: Optional[list[AlternateTitle]] = field(
        default=None, validator=optional(list_of(AlternateTitle))
    )
    call_numbers: Optional[list[str]] = field(
        default=None, validator=optional(list_of(str))
    )
    citation: Optional[str] = field(default=None, validator=optional(instance_of(str)))
    content_type: Optional[list[str]] = field(
        default=None, validator=optional(list_of(str))
    )
    contents: Optional[list[str]] = field(
        default=None, validator=optional(list_of(str))
    )
    contributors: Optional[list[Contributor]] = field(
        default=None, validator=optional(list_of(Contributor))
    )
    dates: Optional[list[Date]] = field(default=None, validator=optional(list_of(Date)))
    edition: Optional[str] = field(default=None, validator=optional(instance_of(str)))
    file_formats: Optional[list[str]] = field(
        default=None, validator=optional(list_of(str))
    )
    format: Optional[str] = field(default=None, validator=optional(instance_of(str)))
    funding_information: Optional[list[Funder]] = field(
        default=None, validator=optional(list_of(Funder))
    )
    holdings: Optional[list[Holding]] = field(
        default=None, validator=optional(list_of(Holding))
    )
    identifiers: Optional[list[Identifier]] = field(
        default=None, validator=optional(list_of(Identifier))
    )
    languages: Optional[list[str]] = field(
        default=None, validator=optional(list_of(str))
    )
    links: Optional[list[Link]] = field(default=None, validator=optional(list_of(Link)))
    literary_form: Optional[str] = field(
        default=None, validator=optional(instance_of(str))
    )
    locations: Optional[list[Location]] = field(
        default=None, validator=optional(list_of(Location))
    )
    notes: Optional[list[Note]] = field(default=None, validator=optional(list_of(Note)))
    numbering: Optional[str] = field(default=None, validator=optional(instance_of(str)))
    physical_description: Optional[str] = field(
        default=None, validator=optional(instance_of(str))
    )
    publication_frequency: Optional[list[str]] = field(
        default=None, validator=optional(list_of(str))
    )
    publication_information: Optional[list[str]] = field(
        default=None, validator=optional(list_of(str))
    )
    related_items: Optional[list[RelatedItem]] = field(
        default=None, validator=optional(list_of(RelatedItem))
    )
    rights: Optional[list[Rights]] = field(
        default=None, validator=optional(list_of(Rights))
    )
    subjects: Optional[list[Subject]] = field(
        default=None, validator=optional(list_of(Subject))
    )
    summary: Optional[list[str]] = field(default=None, validator=optional(list_of(str)))

    def asdict(self):
        return asdict(self, filter=lambda attr, value: value is not None)
