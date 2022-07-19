from transmogrifier.helpers import parse_xml_records
from transmogrifier.sources.whoas import Whoas


def test_valid_content_types_with_all_invalid():
    content_types = ["Book", "Thesis"]
    assert Whoas.valid_content_types(content_types) is False


def test_valid_content_types_with_some_invalid():
    content_types = ["Preprint", "Dataset"]
    assert Whoas.valid_content_types(content_types) is True


def test_valid_content_types_with_all_valid():
    content_types = ["Dataset", "Image"]
    assert Whoas.valid_content_types(content_types) is True


def test_whoas_skips_records_with_only_invalid_content_types():
    input_records = list(
        parse_xml_records(
            "tests/fixtures/dspace/whoas_records_with_valid_and_invalid_content_types.xml"
        )
    )
    assert len(input_records) == 3
    output_records = Whoas("whoas", iter(input_records))
    assert len(list(output_records)) == 2
