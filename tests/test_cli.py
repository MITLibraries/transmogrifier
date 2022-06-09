from transmogrifier.cli import main


def test_cli_with_env(caplog, monkeypatch, runner, tmp_path):
    monkeypatch.setenv("SENTRY_DSN", "https://1234567890@00000.ingest.sentry.io/123456")
    monkeypatch.setenv("WORKSPACE", "test")
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
    assert "Running transmogrifier with env=test and log level=INFO" in caplog.text
    assert (
        "Sentry DSN found, exceptions will be sent to Sentry with env=test"
        in caplog.text
    )
    assert "Running transform for source jpal" in caplog.text
    assert "Completed transform, total record count: 38" in caplog.text


def test_cli_without_env(caplog, monkeypatch, runner, tmp_path):
    monkeypatch.delenv("SENTRY_DSN", raising=False)
    monkeypatch.delenv("WORKSPACE", raising=False)
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
    assert "Running transmogrifier with env=None and log level=DEBUG" in caplog.text
    assert "Sentry DSN found" not in caplog.text


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


def test_cli_whoas(caplog, monkeypatch, runner, tmp_path):
    with caplog.at_level("INFO"):
        outfile = tmp_path / "timdex_whoas_records.json"
        result = runner.invoke(
            main,
            [
                "-i",
                "tests/fixtures/datacite/dspace_dim_records.xml",
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
