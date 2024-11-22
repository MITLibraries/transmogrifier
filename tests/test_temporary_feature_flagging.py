# ruff: noqa: PLR2004

from unittest.mock import patch

import pytest

from transmogrifier.cli import main
from transmogrifier.config import get_etl_version

# NOTE: FEATURE FLAG: this test file can be removed completely after v2 parquet work.


@pytest.fixture
def mocked_v1_write_method():
    with patch(
        "transmogrifier.cli.Transformer.transform_and_write_output_files"
    ) as mocked_method:
        yield mocked_method


@pytest.fixture
def mocked_v2_write_method():
    with patch(
        "transmogrifier.cli.Transformer.write_to_parquet_dataset"
    ) as mocked_method:
        yield mocked_method


def test_etl_version_helper_function_no_env_var_is_v1(monkeypatch):
    monkeypatch.delenv("ETL_VERSION")
    assert get_etl_version() == 1


def test_etl_version_helper_function_env_var_is_1_is_v1(monkeypatch):
    monkeypatch.setenv("ETL_VERSION", "1")
    assert get_etl_version() == 1


def test_etl_version_helper_function_env_var_is_2_is_v2(monkeypatch):
    monkeypatch.setenv("ETL_VERSION", "2")
    assert get_etl_version() == 2


@pytest.mark.parametrize(
    "env_value",
    [
        "pumpkin_pie",  # throws ValueError because not integer
        "3",  # throws ValueError because not 1 or 2
    ],
)
def test_etl_version_helper_function_env_var_value_is_unsupported(env_value, monkeypatch):
    monkeypatch.setenv("ETL_VERSION", env_value)
    with pytest.raises(ValueError):  # noqa: PT011
        get_etl_version()


def test_cli_etl_version_v1_invokes_v1_code(
    mocked_v1_write_method, monkeypatch, runner, tmp_path
):
    monkeypatch.setenv("ETL_VERSION", "1")
    mocked_v1_write_method.side_effect = Exception("Do not proceed")
    runner.invoke(
        main,
        [
            "-i",
            "/does/not/exist/alma-2023-01-13-full-extracted-records-to-index_01.xml",
            "-o",
            "/does/not/exist/libguides.json",
            "-s",
            "libguides",
        ],
    )
    mocked_v1_write_method.assert_called()


def test_cli_etl_version_v2_invokes_v2_code(
    mocked_v2_write_method, monkeypatch, runner, tmp_path
):
    monkeypatch.setenv("ETL_VERSION", "2")
    mocked_v2_write_method.side_effect = Exception("Do not proceed")
    runner.invoke(
        main,
        [
            "-i",
            "/does/not/exist/alma-2023-01-13-full-extracted-records-to-index_01.xml",
            "-o",
            "/does/not/exist/dataset",
            "-s",
            "libguides",
        ],
    )
    mocked_v2_write_method.assert_called()
