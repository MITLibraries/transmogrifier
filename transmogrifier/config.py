"""transmogrifier.config module."""
import json
import logging
import os
from importlib import import_module
from typing import Literal, Union

import sentry_sdk
from bs4 import BeautifulSoup, Tag

logger = logging.getLogger(__name__)

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


def load_external_config(
    file_path: str, file_type: Literal["json", "xml"]
) -> Union[dict, Tag]:
    """
    Return dict from a JSON or XML config file. Logs a warning if a different file_type
    parameter is passed.

    """
    with open(file_path, "rb") as config_file:
        if file_type == "json":
            return json.load(config_file)
        elif file_type == "xml":
            return BeautifulSoup(config_file, "xml")
        else:
            logger.error("Unrecognized file_type parameter: %s", file_type)
            return {}


def create_dict_from_loc_xml_config(
    xml: Tag, element_tag: str, code_tag: str, label_tag: str
) -> dict:
    """
    Return dict from XML object that is formatted like the country and language code
    XML files hosted by Library of Congress. It captures all authorized and obsolete
    codes in a file.

     Args:
            xml: A BeautifulSoup Tag representing an XML config file.
            element_tag: The element representing an item in the crosswalk, e.g.
            language, country.
            code_tag: The element containing a code for the item.
            label_tag: The element containing the preferred label for the item.
    """
    config_dict = {}
    for code_element in xml.find_all(code_tag):
        for parent in [
            parent for parent in code_element.parents if parent.name == element_tag
        ]:
            config_dict[str(code_element.string)] = str(parent.find(label_tag).string)
    return config_dict
