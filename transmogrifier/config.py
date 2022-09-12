"""transmogrifier.config module."""
import json
import logging
import os
from importlib import import_module

import sentry_sdk

SOURCES = {
    "aspace": {
        "name": "MIT ArchivesSpace",
        "base_url": "https://archivesspace.mit.edu/",
        "transform-class": "transmogrifier.sources.ead.Ead",
    },
    "dspace": {
        "name": "DSpace@MIT",
        "base_url": "https://dspace.mit.edu/handle/",
        "transform-class": "transmogrifier.sources.dspace_mets.DspaceMets",
    },
    "jpal": {
        "name": "Abdul Latif Jameel Poverty Action Lab Dataverse",
        "base_url": "https://dataverse.harvard.edu/dataset.xhtml?persistentId=",
        "transform-class": "transmogrifier.sources.datacite.Datacite",
    },
    "whoas": {
        "name": "Woods Hole Open Access Server",
        "base_url": "https://darchive.mblwhoilibrary.org/handle/",
        "transform-class": "transmogrifier.sources.whoas.Whoas",
    },
    "zenodo": {
        "name": "Zenodo",
        "base_url": "https://zenodo.org/record/",
        "transform-class": "transmogrifier.sources.zenodo.Zenodo",
    },
}


def configure_logger(logger: logging.Logger, verbose: bool) -> str:
    if verbose:
        logging.basicConfig(
            format="%(asctime)s %(levelname)s %(name)s.%(funcName)s() line %(lineno)d: "
            "%(message)s",
        )
        logger.setLevel(logging.DEBUG)
        for handler in logging.root.handlers:
            handler.addFilter(logging.Filter("transmogrifier"))
    else:
        logging.basicConfig(
            format="%(asctime)s %(levelname)s %(name)s.%(funcName)s(): %(message)s"
        )
        logger.setLevel(logging.INFO)
    return (
        f"Logger '{logger.name}' configured with level="
        f"{logging.getLevelName(logger.getEffectiveLevel())}"
    )


def configure_sentry() -> str:
    env = os.getenv("WORKSPACE")
    sentry_dsn = os.getenv("SENTRY_DSN")
    if sentry_dsn and sentry_dsn.lower() != "none":
        sentry_sdk.init(sentry_dsn, environment=env)
        return f"Sentry DSN found, exceptions will be sent to Sentry with env={env}"
    return "No Sentry DSN found, exceptions will not be sent to Sentry"


def get_transformer(source: str) -> type:
    """
    Return configured transformer class for a source.

    Source must be configured with a valid transform class path.
    """
    module_name, class_name = SOURCES[source]["transform-class"].rsplit(".", 1)
    source_module = import_module(module_name)
    return getattr(source_module, class_name)


def load_external_config(path: str) -> dict:
    """
    Return dict from JSON config file.

    """
    with open(path, "rb") as json_file:
        return json.load(json_file)
