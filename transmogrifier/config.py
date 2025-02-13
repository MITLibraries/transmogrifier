"""transmogrifier.config module."""

import json
import logging
import os
from typing import Literal

import sentry_sdk
from bs4 import BeautifulSoup  # type: ignore[import-untyped]

logger = logging.getLogger(__name__)

DATE_FORMATS = [
    "%Y",  # strict_year
    "%Y-%m",  # strict_year_month
    # date variations
    "%y-%m",
    "%y-%m-%d",
    "%Y-%m-%d",
    # basic_date variations
    "%y%m%d",
    "%Y%m%d",
    # custom formats
    "%m/%d/%y",
    "%m/%d/%Y",
    "%Y/%m/%d",
    # date_optional_time variations
    "%yT%H",
    "%yT%HZ",
    "%yT%H:%M",
    "%yT%H:%MZ",
    "%yT%H:%M:%S",
    "%yT%H:%M:%SZ",
    "%yT%H:%M:%S.%f",
    "%yT%H:%M:%S.%fZ",
    "%y-%mT%H",
    "%y-%mT%HZ",
    "%y-%mT%H:%M",
    "%y-%mT%H:%MZ",
    "%y-%mT%H:%M:%S",
    "%y-%mT%H:%M:%SZ",
    "%y-%mT%H:%M:%S.%f",
    "%y-%mT%H:%M:%S.%fZ",
    "%y-%m-%dT%H",
    "%y-%m-%dT%HZ",
    "%y-%m-%dT%H:%M",
    "%y-%m-%dT%H:%MZ",
    "%y-%m-%dT%H:%M:%S",
    "%y-%m-%dT%H:%M:%SZ",
    "%y-%m-%dT%H:%M:%S.%f",
    "%y-%m-%dT%H:%M:%S.%fZ",
    "%YT%H",
    "%YT%HZ",
    "%YT%H:%M",
    "%YT%H:%MZ",
    "%YT%H:%M:%S",
    "%YT%H:%M:%SZ",
    "%YT%H:%M:%S.%f",
    "%YT%H:%M:%S.%fZ",
    "%Y-%mT%H",
    "%Y-%mT%HZ",
    "%Y-%mT%H:%M",
    "%Y-%mT%H:%MZ",
    "%Y-%mT%H:%M:%S",
    "%Y-%mT%H:%M:%SZ",
    "%Y-%mT%H:%M:%S.%f",
    "%Y-%mT%H:%M:%S.%fZ",
    "%Y-%m-%dT%H",
    "%Y-%m-%dT%HZ",
    "%Y-%m-%dT%H:%M",
    "%Y-%m-%dT%H:%MZ",
    "%Y-%m-%dT%H:%M:%S",
    "%Y-%m-%dT%H:%M:%SZ",
    "%Y-%m-%dT%H:%M:%S.%f",
    "%Y-%m-%dT%H:%M:%S.%fZ",
]

SOURCES = {
    "alma": {
        "name": "MIT Alma",
        "base-url": (
            "https://mit.primo.exlibrisgroup.com/discovery/fulldisplay?"
            "vid=01MIT_INST:MIT&docid=alma"
        ),
        "transform-class": "transmogrifier.sources.xml.marc.Marc",
    },
    "aspace": {
        "name": "MIT ArchivesSpace",
        "base-url": "https://archivesspace.mit.edu/",
        "transform-class": "transmogrifier.sources.xml.ead.Ead",
    },
    "dspace": {
        "name": "DSpace@MIT",
        "base-url": "https://dspace.mit.edu/handle/",
        "transform-class": "transmogrifier.sources.xml.dspace_mets.DspaceMets",
    },
    "jpal": {
        "name": "Abdul Latif Jameel Poverty Action Lab Dataverse",
        "base-url": "https://dataverse.harvard.edu/dataset.xhtml?persistentId=",
        "transform-class": "transmogrifier.sources.xml.datacite.Datacite",
    },
    "libguides": {
        "name": "LibGuides",
        "base-url": "https://libguides.mit.edu/",
        "transform-class": "transmogrifier.sources.xml.springshare.SpringshareOaiDc",
    },
    "gismit": {
        "name": "MIT GIS Resources",
        "base-url": "None",
        "transform-class": "transmogrifier.sources.json.aardvark.MITAardvark",
    },
    "gisogm": {
        "name": "OpenGeoMetadata GIS Resources",
        "base-url": "None",
        "transform-class": "transmogrifier.sources.json.aardvark.MITAardvark",
    },
    "researchdatabases": {
        "name": "Research Databases",
        "base-url": "https://libguides.mit.edu/",
        "transform-class": "transmogrifier.sources.xml.springshare.SpringshareOaiDc",
    },
    "whoas": {
        "name": "Woods Hole Open Access Server",
        "base-url": "https://darchive.mblwhoilibrary.org/handle/",
        "transform-class": "transmogrifier.sources.xml.whoas.Whoas",
    },
    "zenodo": {
        "name": "Zenodo",
        "base-url": "https://zenodo.org/record/",
        "transform-class": "transmogrifier.sources.xml.zenodo.Zenodo",
    },
}


def configure_logger(
    root_logger: logging.Logger,
    *,
    verbose: bool = False,
    warning_only_loggers: str | None = None,
) -> str:
    """Configure application via passed application root logger.

    If verbose=True, 3rd party libraries can be quite chatty.  For convenience, they can
    be set to WARNING level by either passing a comma seperated list of logger names to
    'warning_only_loggers' or by setting the env var WARNING_ONLY_LOGGERS.
    """
    if verbose:
        root_logger.setLevel(logging.DEBUG)
        logging_format = (
            "%(asctime)s %(levelname)s %(name)s.%(funcName)s() "
            "line %(lineno)d: %(message)s"
        )
    else:
        root_logger.setLevel(logging.INFO)
        logging_format = "%(asctime)s %(levelname)s %(name)s.%(funcName)s(): %(message)s"

    warning_only_loggers = os.getenv("WARNING_ONLY_LOGGERS", warning_only_loggers)
    if warning_only_loggers:
        for name in warning_only_loggers.split(","):
            logging.getLogger(name).setLevel(logging.WARNING)

    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter(logging_format))
    root_logger.addHandler(handler)

    return (
        f"Logger '{root_logger.name}' configured with level="
        f"{logging.getLevelName(root_logger.getEffectiveLevel())}"
    )


def configure_sentry() -> str:
    env = os.getenv("WORKSPACE")
    sentry_dsn = os.getenv("SENTRY_DSN")
    if sentry_dsn and sentry_dsn.lower() != "none":
        sentry_sdk.init(sentry_dsn, environment=env)
        return f"Sentry DSN found, exceptions will be sent to Sentry with env={env}"
    return "No Sentry DSN found, exceptions will not be sent to Sentry"


def load_external_config(
    file_path: str, file_type: Literal["json", "xml"]
) -> dict | BeautifulSoup:
    """
    Load a configuration file into a Python object. JSON files are parsed into dicts
    and XML files are parsed into BeautifulSoup objects.

    Raises an error if an unhandled file_type parameter is passed.

    """
    with open(file_path, "rb") as config_file:
        if file_type == "json":
            return json.load(config_file)
        elif file_type == "xml":  # noqa: RET505
            return BeautifulSoup(config_file, "xml")
        else:
            message = f"Unrecognized file_type parameter: {file_type}"
            raise ValueError(message)


# NOTE: FEATURE FLAG: function will be removed after v2 work is complete
def get_etl_version() -> Literal[1, 2]:
    etl_version = int(os.environ.get("ETL_VERSION", "1"))
    if etl_version not in [1, 2]:
        message = f"ETL_VERSION '{etl_version}' not supported"
        raise ValueError(message)
    return etl_version  # type: ignore[return-value]
