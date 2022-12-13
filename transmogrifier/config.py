"""transmogrifier.config module."""
import json
import logging
import os
from importlib import import_module
from typing import Union

import sentry_sdk
from bs4 import BeautifulSoup, Tag

SOURCES = {
    "alma": {
        "name": "MIT Alma",
        "base-url": (
            "https://mit.primo.exlibrisgroup.com/discovery/fulldisplay?"
            "vid=01MIT_INST:MIT&docid=alma"
        ),
        "transform-class": "transmogrifier.sources.marc.Marc",
    },
    "aspace": {
        "name": "MIT ArchivesSpace",
        "base-url": "https://archivesspace.mit.edu/",
        "transform-class": "transmogrifier.sources.ead.Ead",
    },
    "dspace": {
        "name": "DSpace@MIT",
        "base-url": "https://dspace.mit.edu/handle/",
        "transform-class": "transmogrifier.sources.dspace_mets.DspaceMets",
    },
    "jpal": {
        "name": "Abdul Latif Jameel Poverty Action Lab Dataverse",
        "base-url": "https://dataverse.harvard.edu/dataset.xhtml?persistentId=",
        "transform-class": "transmogrifier.sources.datacite.Datacite",
    },
    "whoas": {
        "name": "Woods Hole Open Access Server",
        "base-url": "https://darchive.mblwhoilibrary.org/handle/",
        "transform-class": "transmogrifier.sources.whoas.Whoas",
    },
    "zenodo": {
        "name": "Zenodo",
        "base-url": "https://zenodo.org/record/",
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


def load_external_config(file_path: str, file_type: str) -> Union[dict, Tag]:
    """
    Return dict from a config file.

    """
    if file_type == "json":
        with open(file_path, "rb") as json_file:
            return json.load(json_file)
    elif file_type == "xml":
        with open(file_path, "rb") as xml_file:
            return BeautifulSoup(xml_file, "xml")
    else:
        return {}


def create_dict_from_xml_config(
    xml_content: Tag, element_name: str, key_tag: str, value_tag: str
) -> dict:
    """
    Return dict from XML object that is formatted like the country and language code
    XML files hosted by Library of Congress.

    """
    config_dict = {}
    for element in xml_content.find_all(element_name):
        config_dict[element.find(key_tag).string] = element.find(value_tag).string
    return config_dict
