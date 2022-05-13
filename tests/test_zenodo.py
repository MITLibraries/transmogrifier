from transmogrifier.sources.zenodo import Zenodo


def test_zenodo_create_source_link(zenodo_record):
    output_records = Zenodo(
        "zenodo",
        "https://zenodo.org/record/",
        "Zenodo",
        zenodo_record,
    )
    output_record = next(output_records)
    assert output_record.source_link == "https://zenodo.org/record/4291646"
    assert output_record.timdex_record_id == "zenodo:4291646"
