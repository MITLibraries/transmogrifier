"""transmogrifier.config module."""
import logging
import os

import sentry_sdk

SOURCES = {
    "dspace": {"name": "DSpace@MIT", "base_url": "https://dspace.mit.edu/"},
    "jpal": {
        "name": "Abdul Latif Jameel Poverty Action Lab Dataverse",
        "base_url": "https://dataverse.harvard.edu/dataset.xhtml?persistentId=",
    },
    "whoas": {
        "name": "Woods Hole Open Access Server",
        "base_url": "https://darchive.mblwhoilibrary.org/handle/",
    },
    "zenodo": {
        "name": "Zenodo",
        "base_url": "https://zenodo.org/record/",
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
