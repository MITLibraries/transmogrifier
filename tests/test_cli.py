from transmogrifier.cli import main


def test_transform_no_sentry_not_verbose(caplog, monkeypatch, runner, tmp_path):
    monkeypatch.delenv("SENTRY_DSN", raising=False)
    outfile = tmp_path / "timdex_jpal_records.json"
    result = runner.invoke(
        main,
        [
            "-i",
            "tests/fixtures/datacite/datacite_records.xml",
            "-o",
            outfile,
            "-s",
            "jpal",
        ],
    )
    assert result.exit_code == 0
    assert "Logger 'root' configured with level=INFO" in caplog.text
    assert "No Sentry DSN found, exceptions will not be sent to Sentry" in caplog.text
    assert "Running transform for source jpal" in caplog.text
    assert (
        "Completed transform, total records processed: 38, transformed records: 38"
        ", skipped records: 0"
    ) in caplog.text
    assert "Total time to complete transform" in caplog.text


def test_transform_with_sentry_and_verbose(caplog, monkeypatch, runner, tmp_path):
    monkeypatch.setenv("SENTRY_DSN", "https://1234567890@00000.ingest.sentry.io/123456")
    monkeypatch.setenv("STATUS_UPDATE_INTERVAL", "10")
    outfile = tmp_path / "timdex_jpal_records.json"
    result = runner.invoke(
        main,
        [
            "-i",
            "tests/fixtures/datacite/datacite_records.xml",
            "-o",
            outfile,
            "-s",
            "jpal",
            "-v",
        ],
    )
    assert result.exit_code == 0
    assert "Logger 'root' configured with level=DEBUG" in caplog.text
    assert (
        "Sentry DSN found, exceptions will be sent to Sentry with env=test"
        in caplog.text
    )
    assert "Running transform for source jpal" in caplog.text
    assert "Status update: 30 records written to output file so far!" in caplog.text
    assert (
        "Completed transform, total records processed: 38, transformed records: 38"
        ", skipped records: 0"
    ) in caplog.text


def test_transform_no_records(runner, tmp_path):
    outfile = tmp_path / "no_records.json"
    result = runner.invoke(
        main,
        [
            "-i",
            "tests/fixtures/no_records.xml",
            "-o",
            outfile,
            "-s",
            "dspace",
        ],
    )
    assert result.exit_code == 1
    assert isinstance(result.exception, ValueError)
