from transmogrifier.cli import main


def test_cli_with_env(caplog, monkeypatch, runner):
    monkeypatch.setenv("LOGGING_LEVEL", "INFO")
    monkeypatch.setenv("SENTRY_DSN", "https://1234567890@00000.ingest.sentry.io/123456")
    monkeypatch.setenv("WORKSPACE", "test")
    with caplog.at_level("INFO"):
        result = runner.invoke(main, ["zenodo"])
        assert result.exit_code == 0
        assert "Running transmogrifier with env=test and log level=INFO" in caplog.text
        assert (
            "Sentry DSN found, exceptions will be sent to Sentry with env=test"
            in caplog.text
        )


def test_cli_without_env(caplog, monkeypatch, runner):
    monkeypatch.delenv("LOGGING_LEVEL", raising=False)
    monkeypatch.delenv("SENTRY_DSN", raising=False)
    monkeypatch.delenv("WORKSPACE", raising=False)
    with caplog.at_level("INFO"):
        result = runner.invoke(main, ["zenodo"])
        assert result.exit_code == 0
        assert "Running transmogrifier with env=None and log level=DEBUG" in caplog.text
