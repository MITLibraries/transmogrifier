# ruff: noqa: PLR2004
from transmogrifier.sources.xml.whoas import Whoas


def test_valid_content_types_with_all_invalid():
    content_types = [
        "Article",
        "authority list",
        "book",
        "book chapter",
        "course",
        "no content type in source record",
        "other",
        "preprint",
        "presentation",
        "Technical report",
        "thesis",
        "text",
        "working paper",
    ]
    assert Whoas.valid_content_types(content_types) is False


def test_valid_content_types_with_some_invalid():
    content_types = ["Preprint", "dataset"]
    assert Whoas.valid_content_types(content_types) is True


def test_valid_content_types_with_all_valid():
    content_types = ["Dataset", "image"]
    assert Whoas.valid_content_types(content_types) is True


def test_whoas_skips_records_with_only_invalid_or_not_present_content_types():
    source_records = list(
        Whoas.parse_source_file(
            "tests/fixtures/dspace/whoas_records_with_valid_and_invalid_content_types.xml"
        )
    )
    assert len(source_records) == 4
    output_records = Whoas("whoas", iter(source_records))
    assert len(list(output_records)) == 2
