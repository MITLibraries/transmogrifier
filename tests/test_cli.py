import subprocess
from unittest import mock

from transmogrifier.cli import main
from transmogrifier.exceptions import CriticalError


def _mock_transformer():
    transformer = mock.MagicMock()
    transformer.processed_record_count = 100
    transformer.transformed_record_count = 100
    transformer.skipped_record_count = 0
    transformer.deleted_records = []
    return transformer


def test_transform_no_sentry_not_verbose(caplog, monkeypatch, runner, tmp_path):
    monkeypatch.delenv("SENTRY_DSN", raising=False)
    with mock.patch(
        "transmogrifier.cli.Transformer.load", return_value=_mock_transformer()
    ):
        result = runner.invoke(
            main,
            [
                "-i",
                "fake-input-file",
                "--output-dataset",
                str(tmp_path),
                "-s",
                "libguides",
            ],
        )
    assert "Logger 'root' configured with level=INFO" in caplog.text
    assert "No Sentry DSN found, exceptions will not be sent to Sentry" in caplog.text
    assert "Total time to complete transform" in caplog.text
    assert result.exit_code == 0


def test_transform_with_sentry_and_verbose(caplog, monkeypatch, runner, tmp_path):
    monkeypatch.setenv("SENTRY_DSN", "https://1234567890@00000.ingest.sentry.io/123456")
    monkeypatch.setenv("STATUS_UPDATE_INTERVAL", "10")
    with mock.patch(
        "transmogrifier.cli.Transformer.load", return_value=_mock_transformer()
    ):
        result = runner.invoke(
            main,
            [
                "-i",
                "fake-input-file",
                "--output-dataset",
                str(tmp_path),
                "-s",
                "libguides",
                "-v",
            ],
        )
    assert "Logger 'root' configured with level=DEBUG" in caplog.text
    assert (
        "Sentry DSN found, exceptions will be sent to Sentry with env=test" in caplog.text
    )
    assert result.exit_code == 0


def test_transform_no_records(
    caplog,
    runner,
    source_input_file,
    empty_source_input_file,
    empty_dataset_location,
):
    caplog.set_level("DEBUG")
    result = runner.invoke(
        main,
        [
            "-i",
            empty_source_input_file,
            "--output-dataset",
            empty_dataset_location,
            "-s",
            "dspace",
        ],
    )
    assert result.exit_code == 0
    assert "Completed transform, total records processed: 0" in caplog.text


def test_transform_deleted_records(
    caplog, runner, source_input_file, empty_dataset_location
):
    result = runner.invoke(
        main,
        [
            "-i",
            source_input_file,
            "--output-dataset",
            empty_dataset_location,
            "-s",
            "jpal",
        ],
    )
    assert result.exit_code == 0
    assert "deleted records: 1" in caplog.text


def test_transform_run_id_argument_passed_and_used(caplog, runner, tmp_path):
    caplog.set_level("INFO")
    run_id = "abc123"
    with mock.patch(
        "transmogrifier.sources.transformer.Transformer.write_to_timdex_dataset",
        autospec=True,
    ) as mocked_transform_and_write:
        mocked_transform_and_write.side_effect = Exception("stopping transformation")
        runner.invoke(
            main,
            [
                "--verbose",
                "-s",
                "alma",
                "-r",
                run_id,
                "-i",
                "tests/fixtures/dataset/libguides-2024-06-03-full-extracted-records-to-index.xml",
                "-o",
                f"{tmp_path}/dataset",
            ],
        )
        transformer = mocked_transform_and_write.call_args.args[0]
        assert transformer.run_data["run_id"] == run_id


def test_transform_run_id_argument_not_passed_and_uuid_minted(caplog, runner, tmp_path):
    caplog.set_level("INFO")
    with (
        mock.patch(
            "transmogrifier.sources.transformer.Transformer.write_to_timdex_dataset",
            autospec=True,
        ) as mocked_transform_and_write,
        mock.patch("transmogrifier.sources.transformer.uuid.uuid4") as mocked_uuid4,
    ):
        mocked_transform_and_write.side_effect = Exception("stopping transformation")
        mocked_uuid4.return_value = "a-really-cool-minted-uuid"
        runner.invoke(
            main,
            [
                "--verbose",
                "-s",
                "alma",
                "-i",
                "tests/fixtures/dataset/libguides-2024-06-03-full-extracted-records-to-index.xml",
                "-o",
                f"{tmp_path}/dataset",
            ],
        )
        transformer = mocked_transform_and_write.call_args.args[0]
        assert transformer.run_data["run_id"] == "a-really-cool-minted-uuid"


def test_transform_run_timestamp_argument_passed_and_used(caplog, runner, tmp_path):
    caplog.set_level("INFO")
    run_timestamp = "2024-06-03T12:34:56"
    with mock.patch(
        "transmogrifier.sources.transformer.Transformer.write_to_timdex_dataset",
        autospec=True,
    ) as mocked_transform_and_write:
        mocked_transform_and_write.side_effect = Exception("stopping transformation")
        runner.invoke(
            main,
            [
                "--verbose",
                "-s",
                "alma",
                "-t",
                run_timestamp,
                "-i",
                "tests/fixtures/dataset/libguides-2024-06-03-full-extracted-records-to-index.xml",
                "-o",
                f"{tmp_path}/dataset",
            ],
        )
        transformer = mocked_transform_and_write.call_args.args[0]
        assert transformer.run_data["run_timestamp"] == run_timestamp
        assert transformer.run_data["run_date"] == "2024-06-03"


def test_transform_run_timestamp_argument_not_passed_and_timestamp_minted(
    caplog, runner, tmp_path
):
    caplog.set_level("INFO")
    mocked_datetime = mock.MagicMock()
    mocked_datetime.now.return_value.isoformat.return_value = "2024-06-03T12:34:56+00:00"
    with (
        mock.patch(
            "transmogrifier.sources.transformer.Transformer.write_to_timdex_dataset",
            autospec=True,
        ) as mocked_transform_and_write,
        mock.patch("transmogrifier.sources.transformer.datetime", mocked_datetime),
    ):
        mocked_transform_and_write.side_effect = Exception("stopping transformation")
        runner.invoke(
            main,
            [
                "--verbose",
                "-s",
                "alma",
                "-i",
                "tests/fixtures/dataset/libguides-2024-06-03-full-extracted-records-to-index.xml",
                "-o",
                f"{tmp_path}/dataset",
            ],
        )
        transformer = mocked_transform_and_write.call_args.args[0]
        assert transformer.run_data["run_timestamp"] == "2024-06-03T12:34:56+00:00"
        assert transformer.run_data["run_date"] == "2024-06-03"


def test_transform_no_memory_fault_for_bs4_parsing(monkeypatch, tmp_path):
    """This test requires running the CLI as a subprocess to simulate the 'uv run ...'
    context. In this context, we have observed memory faults when BeautifulSoup4 is used
    by a source, and the number of records in the run requires multiple batches during
    parquet dataset writing. The exit code associated with this memory fault is -6.
    """
    result = subprocess.run(  # noqa: S603
        [  # noqa: S607
            "uv",
            "run",
            "transform",
            "-s",
            "researchdatabases",
            "-i",
            "tests/fixtures/dataset/libguides-2025-01-09-full-extracted-records-to-index.xml",
            "-o",
            f"{tmp_path}/dataset",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0


def test_transform_no_memory_fault_for_marc_parsing(tmp_path):
    """As test_transform_no_memory_fault_for_bs4_parsing, for lxml parsing.

    Requires one more record than a single parquet dataset write batch.
    """
    record = (
        "<record><leader>03282nam  2200721Ki 4500</leader>"
        '<controlfield tag="001">990027185640106761</controlfield>'
        '<controlfield tag="008">170906s2016    fr mun| o         e zxx d</controlfield>'
        '<datafield tag="245"><subfield code="a">Title</subfield></datafield></record>'
    )
    input_file = tmp_path / "alma-2026-01-01-daily-extracted-records-to-index.xml"
    input_file.write_text(f"<collection>{record * 1001}</collection>")

    result = subprocess.run(  # noqa: S603
        [  # noqa: S607
            "uv",
            "run",
            "transform",
            "-s",
            "alma",
            "-i",
            str(input_file),
            "-o",
            f"{tmp_path}/dataset",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0


def test_transform_critical_error_prevents_writing(
    caplog, runner, source_input_file, source_transformer, empty_dataset_location
):
    caplog.set_level("INFO")

    with (
        mock.patch(
            "transmogrifier.cli.Transformer.load", return_value=source_transformer
        ),
        mock.patch.object(
            source_transformer,
            "get_timdex_record_id",
            side_effect=CriticalError("Catastrophic failure, no records will work!"),
        ),
    ):
        result = runner.invoke(
            main,
            [
                "-s",
                "libguides",
                "-i",
                source_input_file,
                "--output-dataset",
                empty_dataset_location,
            ],
        )

    assert isinstance(result.exception, CriticalError)
    assert str(result.exception) == "Catastrophic failure, no records will work!"
    assert result.exit_code != 0
    assert "Completed transform, total records processed" not in caplog.text


def test_transform_no_input_option_raises_usage_error(runner, tmp_path):
    result = runner.invoke(
        main, ["-s", "alma", "--output-dataset", str(tmp_path / "dataset")]
    )
    assert result.exit_code == 2  # noqa: PLR2004
    assert (
        "Exactly one input option is required: --input-file or --input-dataset or "
        "--input-parquet" in result.output
    )


def test_transform_multiple_input_options_raises_usage_error(runner, tmp_path):
    result = runner.invoke(
        main,
        [
            "-s",
            "alma",
            "--input-file",
            "fake-input-file",
            "--input-parquet",
            "fake-input-parquet",
            "--output-dataset",
            str(tmp_path / "dataset"),
        ],
    )
    assert result.exit_code == 2  # noqa: PLR2004
    assert "Exactly one input option is required" in result.output


def test_transform_no_output_option_raises_usage_error(runner):
    result = runner.invoke(main, ["-s", "alma", "--input-file", "fake-input-file"])
    assert result.exit_code == 2  # noqa: PLR2004
    assert (
        "Exactly one output option is required: --output-file or --output-dataset or "
        "--output-parquet" in result.output
    )


def test_transform_multiple_output_options_raises_usage_error(runner, tmp_path):
    result = runner.invoke(
        main,
        [
            "-s",
            "alma",
            "--input-file",
            "fake-input-file",
            "--output-dataset",
            str(tmp_path / "dataset"),
            "--output-parquet",
            str(tmp_path / "parquet"),
        ],
    )
    assert result.exit_code == 2  # noqa: PLR2004
    assert "Exactly one output option is required" in result.output


def test_transform_input_parquet_and_output_parquet(
    caplog, runner, source_parquet_location, tmp_path
):
    caplog.set_level("INFO")
    output_location = tmp_path / "output"
    result = runner.invoke(
        main,
        [
            "-s",
            "researchdatabases",
            "--input-parquet",
            source_parquet_location,
            "--output-parquet",
            str(output_location),
        ],
    )
    assert result.exit_code == 0
    assert "Parquet files write complete - files: 1" in caplog.text
    assert [path.name for path in output_location.iterdir()] == ["part-0.parquet"]


def test_transform_output_file(caplog, runner, source_input_file, tmp_path):
    caplog.set_level("INFO")
    output_file = tmp_path / "records.jsonl"
    result = runner.invoke(
        main,
        [
            "-s",
            "jpal",
            "--input-file",
            source_input_file,
            "--output-file",
            str(output_file),
        ],
    )
    assert result.exit_code == 0
    assert "deleted records: 1" in caplog.text
    assert f"File write complete - records: 3, file: {output_file}" in caplog.text


def test_transform_workers_option(caplog, runner, source_parquet_location, tmp_path):
    caplog.set_level("INFO")
    result = runner.invoke(
        main,
        [
            "-s",
            "researchdatabases",
            "--input-parquet",
            source_parquet_location,
            "--output-parquet",
            str(tmp_path / "output"),
            "--workers",
            "2",
        ],
    )
    assert result.exit_code == 0
    assert "Transforming records with 2 worker processes" in caplog.text
    assert "Completed transform, total records processed: 3" in caplog.text


def test_transform_workers_option_must_be_positive(runner, tmp_path):
    result = runner.invoke(
        main,
        [
            "-s",
            "alma",
            "--input-file",
            "fake-input-file",
            "--output-dataset",
            str(tmp_path / "dataset"),
            "--workers",
            "0",
        ],
    )
    assert result.exit_code == 2  # noqa: PLR2004
    assert "Invalid value for '-w' / '--workers'" in result.output
