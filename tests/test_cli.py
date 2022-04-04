import logging

from transmogrifier.cli import main


def test_zenodo(
    caplog,
    runner,
):
    with caplog.at_level(logging.INFO):
        result = runner.invoke(
            main,
            ["zenodo"],
        )
        assert result.exit_code == 0
        assert "Initializing app" in caplog.text
        assert "Running zenodo" in caplog.text
