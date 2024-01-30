import logging

import pytest
from bs4 import BeautifulSoup  # type: ignore[import-untyped]

from transmogrifier.config import (
    configure_logger,
    configure_sentry,
    load_external_config,
)


def test_configure_logger_not_verbose():
    logger = logging.getLogger(__name__)
    result = configure_logger(logger, verbose=False)
    assert logger.getEffectiveLevel() == logging.INFO
    assert result == "Logger 'tests.test_config' configured with level=INFO"


def test_configure_logger_verbose(caplog):
    logger = logging.getLogger(__name__)
    result = configure_logger(logger, verbose=True)
    assert logger.getEffectiveLevel() == logging.DEBUG
    assert result == "Logger 'tests.test_config' configured with level=DEBUG"


def test_configure_sentry_no_env_variable(monkeypatch):
    monkeypatch.delenv("SENTRY_DSN", raising=False)
    result = configure_sentry()
    assert result == "No Sentry DSN found, exceptions will not be sent to Sentry"


def test_configure_sentry_env_variable_is_none(monkeypatch):
    monkeypatch.setenv("SENTRY_DSN", "None")
    result = configure_sentry()
    assert result == "No Sentry DSN found, exceptions will not be sent to Sentry"


def test_configure_sentry_env_variable_is_dsn(monkeypatch):
    monkeypatch.setenv("SENTRY_DSN", "https://1234567890@00000.ingest.sentry.io/123456")
    result = configure_sentry()
    assert result == "Sentry DSN found, exceptions will be sent to Sentry with env=test"


def test_load_external_config_invalid_file_type_raises_error():
    with pytest.raises(ValueError, match="Unrecognized file_type parameter: zxr"):
        load_external_config("config/loc-countries.xml", "zxr")


def test_load_external_config_json():
    assert isinstance(
        load_external_config("config/marc_content_type_crosswalk.json", "json"), dict
    )


def test_load_external_config_xml():
    assert type(load_external_config("config/loc-countries.xml", "xml")) == BeautifulSoup
