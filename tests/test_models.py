import pytest

from transmogrifier.models import Contributor, Date, Identifier, Note, TimdexRecord


def test_export_as_json_incorrect_value_types():
    with pytest.raises(TypeError):
        TimdexRecord(
            timdex_record_id="123",
            identifiers=[Identifier(value="123")],
            title=123,
            source="Data Provider",
            source_link="example://example.example",
        )


def test_export_as_json_missing_fields():
    with pytest.raises(TypeError):
        TimdexRecord(
            timdex_record_id="123",
            identifiers=[
                Identifier(
                    value="123",
                )
            ],
            title=None,
            source="Data Provider",
            source_link="example://example.example",
        )


def test_export_as_json_empty_list():
    with pytest.raises(ValueError):
        TimdexRecord(
            timdex_record_id="123",
            identifiers=[],
            title="Dataset 1",
            source="Data Provider",
            source_link="example://example.example",
        )


def test_export_as_json_invalid_date_range():
    with pytest.raises(KeyError):
        TimdexRecord(
            title="Dataset 1",
            timdex_record_id="123",
            identifiers=[Identifier(value="123")],
            source="Data Provider",
            source_link="example://example.example",
            dates=[Date(range={"after": 1901, "before": 1970})],
        )


def test_export_as_json_full(timdex_record_generic_full):
    timdex_record = TimdexRecord(
        timdex_record_id="123",
        identifiers=[Identifier(value="123", kind="DOI")],
        title="Dataset 1",
        source="Data Provider",
        source_link="example://example.example",
        contributors=[
            Contributor(
                value="Smith, Jane",
                kind="author",
                identifier="45678",
                affiliation="University",
                mit_affiliated=True,
            )
        ],
        publication_information=["Harvard Dataverse"],
        dates=[Date(range={"gte": 1901, "lte": 1970})],
        notes=[Note(value="Survey Data", kind="ResourceType")],
        content_type=["Dataset"],
    )
    assert timdex_record.export_as_json() == timdex_record_generic_full


def test_export_as_json_minimal(timdex_record_generic_minimal):
    timdex_record = TimdexRecord(
        timdex_record_id="123",
        title="Dataset 1",
        identifiers=[Identifier(value="123")],
        source="Data Provider",
        source_link="example://example.example",
    )
    assert timdex_record.export_as_json() == timdex_record_generic_minimal


def test_get_instance_attribute_values_empty():
    timdex_record = TimdexRecord(
        timdex_record_id="123",
        identifiers=[Identifier(value="123", kind="DOI")],
        title="Dataset 1",
        source="Data Provider",
        source_link="example://example.example",
    )
    assert timdex_record.get_instance_attribute_values("dates") == []


def test_get_instance_attribute_values_full():
    timdex_record = TimdexRecord(
        timdex_record_id="123",
        identifiers=[Identifier(value="123", kind="DOI")],
        title="Dataset 1",
        source="Data Provider",
        source_link="example://example.example",
    )
    assert timdex_record.get_instance_attribute_values("identifiers") == [
        {"kind": "DOI", "value": "123"}
    ]
