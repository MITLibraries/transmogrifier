from transmogrifier.sources.jpal import create_timdex_json_from_jpal_xml


def test_create_timdex_json_from_jpal_xml_full(
    timdex_record_jpal_full, datacite_record_jpal_full
):
    timdex_record = create_timdex_json_from_jpal_xml(datacite_record_jpal_full)
    assert timdex_record.export_as_json() == timdex_record_jpal_full


def test_create_timdex_json_record_from_jpal_xml_minimal(
    timdex_record_jpal_minimal, datacite_record_jpal_minimal
):
    timdex_record = create_timdex_json_from_jpal_xml(datacite_record_jpal_minimal)
    assert timdex_record.export_as_json() == timdex_record_jpal_minimal
