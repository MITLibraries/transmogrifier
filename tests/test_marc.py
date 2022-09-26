import transmogrifier.models as timdex
from transmogrifier.helpers import parse_xml_records
from transmogrifier.sources.marc import Marc


def test_marc_record_all_fields_transform_correctly():
    marc_xml_records = parse_xml_records(
        "tests/fixtures/marc/marc_record_all_fields.xml", "record"
    )
    output_records = Marc("alma", marc_xml_records)
    assert next(output_records) == timdex.TimdexRecord(
        source="MIT Alma",
        source_link=(
            "https://mit.primo.exlibrisgroup.com/discovery/fulldisplay?vid="
            "01MIT_INST:MIT&docid=alma990027185640106761"
        ),
        timdex_record_id="alma:990027185640106761",
        title="Célébration : 10 siècles de musique de noël.",
        alternate_titles=[
            timdex.AlternateTitle(
                value="Main Entry Uniform Title.", kind="Main Entry - Uniform Title"
            ),
            timdex.AlternateTitle(value="Uniform Title.", kind="Uniform Title"),
            timdex.AlternateTitle(
                value="Varying Form Of Title.", kind="Varying Form of Title"
            ),
            timdex.AlternateTitle(
                value="Added Entry Uniform Title.",
                kind="Added Entry - Uniform Title",
            ),
            timdex.AlternateTitle(
                value="Added Entry Uncontrolled Related/Analytical Title.",
                kind="Added Entry - Uncontrolled Related/Analytical Title",
            ),
        ],
        call_numbers=["MA123.4", "123.45"],
        citation=(
            "Célébration : 10 siècles de musique de noël.. "
            "https://mit.primo.exlibrisgroup.com/discovery/fulldisplay?vid="
            "01MIT_INST:MIT&docid=alma990027185640106761"
        ),
        content_type=["Not specified"],
        literary_form="Nonfiction",
    )


def test_marc_record_attribute_and_subfield_variations_transforms_correctly():
    marc_xml_records = parse_xml_records(
        "tests/fixtures/marc/marc_record_attribute_and_subfield_variations.xml",
        "record",
    )
    output_records = Marc("alma", marc_xml_records)
    assert next(output_records) == timdex.TimdexRecord(
        source="MIT Alma",
        source_link=(
            "https://mit.primo.exlibrisgroup.com/discovery/fulldisplay?vid="
            "01MIT_INST:MIT&docid=alma990027185640106761"
        ),
        timdex_record_id="alma:990027185640106761",
        title="a b f g k n p s",
        alternate_titles=[
            timdex.AlternateTitle(
                value="a d f g h k l m n o p r s t",
                kind="Main Entry - Uniform Title",
            ),
            timdex.AlternateTitle(
                value="a d f g h k l m n o p r s", kind="Uniform Title"
            ),
            timdex.AlternateTitle(
                value="a b f g h i n p", kind="Varying Form of Title"
            ),
            timdex.AlternateTitle(
                value="a d f g h i k l m n o p r s t",
                kind="Added Entry - Uniform Title",
            ),
            timdex.AlternateTitle(
                value="a n p",
                kind="Added Entry - Uncontrolled Related/Analytical Title",
            ),
        ],
        call_numbers=["a", "a"],
        citation=(
            "a b f g k n p s. https://mit.primo.exlibrisgroup.com/discovery/"
            "fulldisplay?vid=01MIT_INST:MIT&docid=alma990027185640106761"
        ),
        content_type=["Not specified"],
    )


def test_marc_record_with_blank_optional_fields_transforms_correctly():
    marc_xml_records = parse_xml_records(
        "tests/fixtures/marc/marc_record_blank_optional_fields.xml", "record"
    )
    output_records = Marc("alma", marc_xml_records)
    assert next(output_records) == timdex.TimdexRecord(
        source="MIT Alma",
        source_link=(
            "https://mit.primo.exlibrisgroup.com/discovery/fulldisplay?vid="
            "01MIT_INST:MIT&docid=alma990027185640106761"
        ),
        timdex_record_id="alma:990027185640106761",
        title="Title not provided",
        citation=(
            "Title not provided. https://mit.primo.exlibrisgroup.com/discovery/"
            "fulldisplay?vid=01MIT_INST:MIT&docid=alma990027185640106761"
        ),
        content_type=["Not specified"],
    )


def test_marc_record_with_missing_optional_fields_transforms_correctly():
    marc_xml_records = parse_xml_records(
        "tests/fixtures/marc/marc_record_missing_optional_fields.xml", "record"
    )
    output_records = Marc("alma", marc_xml_records)
    assert next(output_records) == timdex.TimdexRecord(
        source="MIT Alma",
        source_link="https://mit.primo.exlibrisgroup.com/discovery/fulldisplay?vid="
        "01MIT_INST:MIT&docid=alma990027185640106761",
        timdex_record_id="alma:990027185640106761",
        title="Title not provided",
        citation=(
            "Title not provided. https://mit.primo.exlibrisgroup.com/discovery/"
            "fulldisplay?vid=01MIT_INST:MIT&docid=alma990027185640106761"
        ),
        content_type=["Not specified"],
    )


def test_get_main_titles_record_with_title():
    marc_xml_records = parse_xml_records(
        "tests/fixtures/marc/marc_record_all_fields.xml", "record"
    )
    assert Marc.get_main_titles(next(marc_xml_records)) == [
        "Célébration : 10 siècles de musique de noël."
    ]


def test_get_main_titles_record_with_blank_title():
    marc_xml_records = parse_xml_records(
        "tests/fixtures/marc/marc_record_blank_optional_fields.xml", "record"
    )
    assert Marc.get_main_titles(next(marc_xml_records)) == []


def test_get_main_titles_record_without_title():
    marc_xml_records = parse_xml_records(
        "tests/fixtures/marc/marc_record_missing_optional_fields.xml", "record"
    )
    assert Marc.get_main_titles(next(marc_xml_records)) == []


def test_get_source_record_id():
    marc_xml_records = parse_xml_records(
        "tests/fixtures/marc/marc_record_all_fields.xml", "record"
    )
    assert Marc.get_source_record_id(next(marc_xml_records)) == "990027185640106761"


def test_create_subfield_value_list_from_datafield_with_values():
    marc_xml_records = parse_xml_records(
        "tests/fixtures/marc/marc_record_all_fields.xml", "record"
    )
    datafield = next(marc_xml_records).find_all("datafield", tag="130")[0]
    assert Marc.create_subfield_value_list_from_datafield(datafield, "ad") == [
        "Main Entry",
        "Uniform Title.",
    ]


def test_create_subfield_value_list_from_datafield_with_blank_values():
    marc_xml_records = parse_xml_records(
        "tests/fixtures/marc/marc_record_blank_optional_fields.xml", "record"
    )
    datafield = next(marc_xml_records).find_all("datafield", tag="130")[0]
    assert Marc.create_subfield_value_list_from_datafield(datafield, "ad") == []


def test_create_subfield_value_string_from_datafield_with_values():
    marc_xml_records = parse_xml_records(
        "tests/fixtures/marc/marc_record_all_fields.xml", "record"
    )
    datafield = next(marc_xml_records).find_all("datafield", tag="130")[0]
    assert (
        Marc.create_subfield_value_string_from_datafield(datafield, "ad", " ")
        == "Main Entry Uniform Title."
    )


def test_create_subfield_value_string_from_datafield_with_blank_values():
    marc_xml_records = parse_xml_records(
        "tests/fixtures/marc/marc_record_blank_optional_fields.xml", "record"
    )
    datafield = next(marc_xml_records).find_all("datafield", tag="130")[0]
    assert Marc.create_subfield_value_string_from_datafield(datafield, "ad") == ""
