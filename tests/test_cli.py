from transmogrifier.cli import main


def test_cli_jpal_no_sentry_not_verbose(caplog, monkeypatch, runner, tmp_path):
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
    assert "Completed transform, total record count: 38" in caplog.text
    assert "Total time to complete transform" in caplog.text


def test_cli_jpal_with_sentry_and_verbose(caplog, monkeypatch, runner, tmp_path):
    monkeypatch.setenv("SENTRY_DSN", "https://1234567890@00000.ingest.sentry.io/123456")
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
    assert "Completed transform, total record count: 38" in caplog.text


def test_cli_no_records(caplog, runner, tmp_path):
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


def test_cli_dspace_mets(caplog, runner, tmp_path):
    outfile = tmp_path / "timdex_dspace_records.json"
    result = runner.invoke(
        main,
        [
            "-i",
            "tests/fixtures/dspace/dspace_mets_records.xml",
            "-o",
            outfile,
            "-s",
            "dspace",
        ],
    )
    assert result.exit_code == 0
    assert "Completed transform, total record count: 12" in caplog.text


def test_cli_whoas(caplog, runner, tmp_path):
    outfile = tmp_path / "timdex_whoas_records.json"
    result = runner.invoke(
        main,
        [
            "-i",
            "tests/fixtures/dspace/dspace_dim_records.xml",
            "-o",
            outfile,
            "-s",
            "whoas",
            "-v",
        ],
    )
    assert result.exit_code == 0
    assert "Running transform for source whoas" in caplog.text
    assert "Completed transform, total record count: 5" in caplog.text


def test_cli_zenodo(caplog, runner, tmp_path):
    outfile = tmp_path / "timdex_jpal_records.json"
    result = runner.invoke(
        main,
        [
            "-i",
            "tests/fixtures/datacite/datacite_records.xml",
            "-o",
            outfile,
            "-s",
            "zenodo",
        ],
    )
    assert result.exit_code == 0
    assert "Running transform for source zenodo" in caplog.text
    assert "Completed transform, total record count: 38" in caplog.text
