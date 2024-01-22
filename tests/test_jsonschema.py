import json
import os

from attrs import asdict
from jsonschema import validate, ValidationError, FormatChecker, Draft202012Validator

schema = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "title": "MIT Schema - TIMDEX",
    "description": "Schema for MIT TIMDEX record",
    "type": "object",
    "properties": {
        "source": {"type": "string"},
        "source_link": {"type": "string"},
        "timdex_record_id": {"type": "string"},
        "title": {"type": "string"},
        "alternate_titles": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {"value": {"type": "string"}, "kind": {"type": "string"}},
                "required": ["value"],
            },
        },
        "call_numbers": {"$ref": "#/$defs/list_of_strings"},
        "citation": {"type": "string"},
        "content_type": {"$ref": "#/$defs/list_of_strings"},
        "contents": {"$ref": "#/$defs/list_of_strings"},
        "contributors": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "value": {"type": "string"},
                    "affiliation": {"$ref": "#/$defs/list_of_strings"},
                    "kind": {"type": "string"},
                    "mit_affiliated": {"type": "boolean"},
                },
                "required": ["value"],
            },
        },
        "dates": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "kind": {"type": "string"},
                    "note": {"type": "string"},
                    "range": {
                        "type": "object",
                        "properties": {
                            "gt": {"type": "string"},
                            "gte": {"type": "string"},
                            "lt": {"type": "string"},
                            "lte": {"type": "string"},
                        },
                    },
                    "value": {
                        "anyOf": [
                            {"$ref": "#/$defs/strict_year"},
                            {"pattern": r"^\d{4}-(0?[1-9]|1[0,1,2])$"},
                            {"format": "date"},
                        ],
                    },
                },
            },
        },
        "edition": {"type": "string"},
        "file_formats": {"$ref": "#/$defs/list_of_strings"},
        "format": {"type": "string"},
        "funding_information": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "funder_name": {"type": "string"},
                    "funder_identifier": {"type": "string"},
                    "funder_identifier_type": {"type": "string"},
                    "award_number": {"type": "string"},
                    "award_uri": {"type": "string"},
                },
            },
        },
        "holdings": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "call_number": {"type": "string"},
                    "collection": {"type": "string"},
                    "format": {"type": "string"},
                    "location": {"type": "string"},
                    "note": {"type": "string"},
                },
            },
        },
        "identifiers": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {"value": {"type": "string"}, "kind": {"type": "string"}},
                "required": ["value"],
            },
        },
        "languages": {"$ref": "#/$defs/list_of_strings"},
        "links": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "url": {"type": "string"},
                    "kind": {"type": "string"},
                    "restrictions": {"type": "string"},
                    "text": {"type": "string"},
                },
                "required": ["url"],
            },
        },
        "literary_form": {"type": "string"},
        "locations": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "value": {"type": "string"},
                    "kind": {"type": "string"},
                    "geodata": {"type": "array", "items": {"type": "number"}},
                },
            },
        },
        "notes": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "value": {"type": "array", "items": {"type": "string"}},
                    "kind": {"type": "string"},
                },
                "required": ["value"],
            },
        },
        "numbering": {"type": "string"},
        "physical_description": {"type": "string"},
        "publication_frequency": {"$ref": "#/$defs/list_of_strings"},
        "publication_information": {"$ref": "#/$defs/list_of_strings"},
        "related_items": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "description": {"type": "string"},
                    "item_type": {"type": "string"},
                    "relationship": {"type": "string"},
                    "uri": {"type": "string"},
                },
            },
        },
        "rights": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "description": {"type": "string"},
                    "kind": {"type": "string"},
                    "uri": {"type": "string"},
                },
            },
        },
        "subjects": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "value": {"$ref": "#/$defs/list_of_strings"},
                    "kind": {"type": "string"},
                },
                "required": ["value"],
            },
        },
        "summary": {"$ref": "#/$defs/list_of_strings"},
    },
    "required": ["source", "source_link", "timdex_record_id", "title"],
    "$defs": {
        "list_of_strings": {"type": "array", "items": {"type": "string"}},
        "strict_year": {"type": "string", "pattern": "^\\d{4}$"},
    },
}


def test_timdex_record_required_fields_jsonschema_validation_success(
    timdex_record_required_fields,
):
    schema_dir = os.path.dirname(os.path.dirname(__file__))
    with open(schema_dir + "/config/mit-schema-timdex-opensearch.json") as f:
        schema = json.loads(f.read())

    timdex_record_required_fields_dict = asdict(
        timdex_record_required_fields,
        filter=lambda _, value: value is not None and value != [],
    )
    validate(
        instance=timdex_record_required_fields_dict,
        schema=schema,
        format_checker=Draft202012Validator.FORMAT_CHECKER,
    )


def test_timdex_record_all_fields_and_subfields_jsonschema_validation_success(
    timdex_record_all_fields_and_subfields,
):
    schema_dir = os.path.dirname(os.path.dirname(__file__))
    with open(schema_dir + "/config/mit-schema-timdex-opensearch.json") as f:
        schema = json.loads(f.read())

    timdex_record_all_fields_and_subfields_dict = asdict(
        timdex_record_all_fields_and_subfields,
        filter=lambda _, value: value is not None and value != [],
    )
    validate(
        instance=timdex_record_all_fields_and_subfields_dict,
        schema=schema,
        format_checker=Draft202012Validator.FORMAT_CHECKER,
    )
