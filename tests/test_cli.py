import subprocess
from unittest import mock

from transmogrifier.cli import main


def test_transform_no_sentry_not_verbose(
    caplog, monkeypatch, runner, libguides_input_file, empty_dataset_location
):
    monkeypatch.delenv("SENTRY_DSN", raising=False)
    result = runner.invoke(
        main,
        [
            "-i",
            libguides_input_file,
            "--output-location",
            empty_dataset_location,
            "-s",
            "libguides",
        ],
    )
    assert result.exit_code == 0
    assert "Logger 'root' configured with level=INFO" in caplog.text
    assert "No Sentry DSN found, exceptions will not be sent to Sentry" in caplog.text
    assert "Running transform for source libguides" in caplog.text
    assert ("Completed transform, total records processed: 4") in caplog.text
    assert "Total time to complete transform" in caplog.text


def test_transform_with_sentry_and_verbose(
    caplog, monkeypatch, runner, libguides_input_file, empty_dataset_location
):
    monkeypatch.setenv("SENTRY_DSN", "https://1234567890@00000.ingest.sentry.io/123456")
    monkeypatch.setenv("STATUS_UPDATE_INTERVAL", "10")
    result = runner.invoke(
        main,
        [
            "-i",
            libguides_input_file,
            "--output-location",
            empty_dataset_location,
            "-s",
            "libguides",
            "-v",
        ],
    )
    assert result.exit_code == 0
    assert "Logger 'root' configured with level=DEBUG" in caplog.text
    assert (
        "Sentry DSN found, exceptions will be sent to Sentry with env=test" in caplog.text
    )
    assert "Running transform for source libguides" in caplog.text
    assert ("Completed transform, total records processed: 4") in caplog.text


def test_transform_no_records(
    caplog,
    runner,
    libguides_input_file,
    empty_libguides_input_file,
    empty_dataset_location,
):
    caplog.set_level("DEBUG")
    result = runner.invoke(
        main,
        [
            "-i",
            empty_libguides_input_file,
            "--output-location",
            empty_dataset_location,
            "-s",
            "dspace",
        ],
    )
    assert result.exit_code == 0
    assert "Completed transform, total records processed: 0" in caplog.text


def test_transform_deleted_records(
    caplog, runner, libguides_input_file, empty_dataset_location
):
    result = runner.invoke(
        main,
        [
            "-i",
            libguides_input_file,
            "--output-location",
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
        "transmogrifier.sources.transformer.Transformer.write_to_parquet_dataset"
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
    assert f"run_id set: '{run_id}'" in caplog.text


def test_transform_run_id_argument_not_passed_and_uuid_minted(caplog, runner, tmp_path):
    caplog.set_level("INFO")
    with mock.patch(
        "transmogrifier.sources.transformer.Transformer.write_to_parquet_dataset"
    ) as mocked_transform_and_write:
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
    assert "explicit run_id not passed, minting new UUID" in caplog.text
    assert "run_id set:" in caplog.text


def test_transform_run_timestamp_argument_passed_and_used(caplog, runner, tmp_path):
    caplog.set_level("INFO")
    run_timestamp = "2024-06-03T12:34:56"
    with mock.patch(
        "transmogrifier.sources.transformer.Transformer.write_to_parquet_dataset"
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
    assert f"run_timestamp set: '{run_timestamp}'" in caplog.text


def test_transform_run_timestamp_argument_not_passed_and_timestamp_minted(
    caplog, runner, tmp_path
):
    caplog.set_level("INFO")
    with mock.patch(
        "transmogrifier.sources.transformer.Transformer.write_to_parquet_dataset"
    ) as mocked_transform_and_write:
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
    assert "explicit run_id not passed, minting new UUID" in caplog.text
    assert "run_timestamp set: '2024-06-03T00:00:00'" in caplog.text


def test_transform_no_memory_fault_for_threaded_bs4_parsing(monkeypatch, tmp_path):
    """This test requires running the CLI as a subprocess to simulate the 'pipenv run ...'
    context.  In this context, we have observed memory faults when BeautifulSoup4 is used
    by a source, and the number of records in the run requires multiple batches during
    parquet dataset writing.  The exit code associated with this memory fault is -6.
    """
    result = subprocess.run(  # noqa: S603
        [  # noqa: S607
            "pipenv",
            "run",
            "transform",
            "-s",
            "libguides",
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
