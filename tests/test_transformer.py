from transmogrifier.sources.transformer import Transformer


def test_transformer_initializes_with_expected_attributes(datacite_records):
    transformer = Transformer("cool-repo", datacite_records)
    assert transformer.source == "cool-repo"
    assert transformer.source_base_url == "https://example.com/"
    assert transformer.source_name == "A Cool Repository"
    assert transformer.input_records == datacite_records


def test_transformer_iterates_through_all_records(datacite_records):
    output_records = Transformer("jpal", datacite_records)
    assert len(list(output_records)) == 38
