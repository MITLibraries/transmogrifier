import logging

import pytest
from bs4 import BeautifulSoup

from transmogrifier.config import (
    configure_logger,
    configure_sentry,
    get_transformer,
    load_external_config,
)
from transmogrifier.sources.datacite import Datacite


def test_configure_logger_not_verbose():
    logger = logging.getLogger(__name__)
    result = configure_logger(logger, verbose=False)
    assert logger.getEffectiveLevel() == 20
    assert result == "Logger 'test_config' configured with level=INFO"


def test_configure_logger_verbose(caplog):
    logger = logging.getLogger(__name__)
    result = configure_logger(logger, verbose=True)
    assert logger.getEffectiveLevel() == 10
    assert result == "Logger 'test_config' configured with level=DEBUG"


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


def test_get_transformer_returns_correct_class_name():
    assert get_transformer("jpal") == Datacite


def test_get_transformer_source_missing_class_name_raises_error():
    with pytest.raises(KeyError):
        get_transformer("cool-repo")


def test_get_transformer_source_wrong_class_name_raises_error(bad_config):
    with pytest.raises(AttributeError):
        get_transformer("bad-class-name")


def test_get_transformer_source_wrong_module_path_raises_error(bad_config):
    with pytest.raises(ImportError):
        get_transformer("bad-module-path")


def test_load_external_config_invalid_file_type_raises_error():
    with pytest.raises(ValueError):
        load_external_config("config/loc-countries.xml", "zxr")


def test_load_external_config_json():
    assert (
        type(load_external_config("config/marc_content_type_crosswalk.json", "json"))
        == dict
    )


def test_load_external_config_xml():
    assert (
        type(load_external_config("config/loc-countries.xml", "xml")) == BeautifulSoup
    )
