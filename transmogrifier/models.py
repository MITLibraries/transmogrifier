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
class Identifier:
    value: str = field(validator=instance_of(str))  # Required subfield
    kind: Optional[str] = field(default=None, validator=optional(instance_of(str)))


@define
class Note:
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
    content_type: Optional[list[str]] = field(
        default=None, validator=optional(list_of(str))
    )
    contributors: Optional[list[Contributor]] = field(
        default=None, validator=optional(list_of(Contributor))
    )
    dates: Optional[list[Date]] = field(default=None, validator=optional(list_of(Date)))
    identifiers: Optional[list[Identifier]] = field(
        default=None, validator=optional(list_of(Identifier))
    )
    notes: Optional[list[Note]] = field(default=None, validator=optional(list_of(Note)))
    publication_information: Optional[list[str]] = field(
        default=None, validator=optional(list_of(str))
    )

    def asdict(self):
        return asdict(self, filter=lambda attr, value: value is not None)
