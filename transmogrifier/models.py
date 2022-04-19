from typing import Dict, List, Optional

import attr
from attr.validators import instance_of, optional


def contains_valid_date_range(instance, attribute, value):
    return attr.validators.and_(
        attr.validators.deep_iterable(
            member_validator=instance_of(Date),
            iterable_validator=instance_of(list),
        ),
        valid_date_range_keys(value),
    )


def valid_date_range_keys(value):
    for date in value:
        if date.range is not None:
            for key in [k for k in date.range if k not in ["gt", "gte", "lt", "lte"]]:
                raise KeyError(
                    f"Invalid key: '{key}', must be 'gt', 'gte', 'lt', or 'lte'"
                )


def list_of(item_type):
    return attr.validators.and_(
        attr.validators.deep_iterable(
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


@attr.s(auto_attribs=True)
class Contributor:
    value: str = attr.ib(validator=instance_of(str))
    kind: Optional[str] = attr.ib(default=None, validator=optional(instance_of(str)))
    identifier: Optional[str] = attr.ib(
        default=None, validator=optional(instance_of(str))
    )
    affiliation: Optional[str] = attr.ib(
        default=None, validator=optional(instance_of(str))
    )
    mit_affiliated: Optional[bool] = attr.ib(
        default=None, validator=optional(instance_of(bool))
    )


@attr.s(auto_attribs=True)
class Date:
    kind: Optional[str] = attr.ib(default=None, validator=optional(instance_of(str)))
    note: Optional[str] = attr.ib(default=None, validator=optional(instance_of(str)))
    range: Optional[Dict] = attr.ib(default=None, validator=optional(instance_of(Dict)))
    value: Optional[str] = attr.ib(default=None, validator=optional(instance_of(str)))


@attr.s(auto_attribs=True)
class Identifier:
    value: str = attr.ib(validator=instance_of(str))
    kind: Optional[str] = attr.ib(default=None, validator=optional(instance_of(str)))


@attr.s(auto_attribs=True)
class Note:
    value: str = attr.ib(validator=instance_of(str))
    kind: Optional[str] = attr.ib(default=None, validator=optional(instance_of(str)))


@attr.s(auto_attribs=True)
class TimdexRecord:
    timdex_record_id: str = attr.ib(validator=instance_of(str))
    identifiers: List[Identifier] = attr.ib(validator=list_of(Identifier))
    title: str = attr.ib(validator=instance_of(str))
    source: str = attr.ib(validator=instance_of(str))
    source_link: str = attr.ib(validator=instance_of(str))
    contributors: Optional[List[Contributor]] = attr.ib(
        default=None, validator=optional(list_of(Contributor))
    )
    publication_information: Optional[List[str]] = attr.ib(
        default=None,
        validator=optional(instance_of(list)),
    )
    dates: Optional[List[Date]] = attr.ib(
        default=None, validator=optional(contains_valid_date_range)
    )
    notes: Optional[List[Note]] = attr.ib(
        default=None, validator=optional(list_of(Note))
    )
    content_type: Optional[List[str]] = attr.ib(
        default=None,
        validator=optional(instance_of(list)),
    )

    def export_as_json(self) -> Dict[str, str]:
        timdex_json_record = {}
        for value_field in [
            "content_type",
            "publication_information",
            "source",
            "source_link",
            "timdex_record_id",
            "title",
        ]:
            if getattr(self, value_field) is not None:
                timdex_json_record[value_field] = getattr(self, value_field)
        for instance_field in ["contributors", "dates", "identifiers", "notes"]:
            instance_values = self.get_instance_attribute_values(instance_field)
            timdex_json_record[instance_field] = instance_values
        timdex_json_record = {k: v for k, v in timdex_json_record.items() if v}
        return timdex_json_record

    def get_instance_attribute_values(self, instance_field: str) -> list[Dict]:
        """
        Retrieve the attribute values from an instance field as a list of dicts.
        Args:
            instance_field: The instance field from which to get the attribute values.
        """
        instance_values = []
        if getattr(self, instance_field) is not None:
            for field in getattr(self, instance_field):
                filtered_instance_values = dict(
                    [(k, v) for k, v in field.__dict__.items() if v is not None]
                )
                instance_values.append(filtered_instance_values)
        return instance_values
