import logging
import os

import click
import sentry_sdk

from transmogrifier.config import SOURCES
from transmogrifier.helpers import parse_xml_records, write_timdex_records_to_json
from transmogrifier.sources.datacite import Datacite
from transmogrifier.sources.dspace_dim import DSpaceDim
from transmogrifier.sources.dspace_mets import DspaceMets
from transmogrifier.sources.zenodo import Zenodo

logger = logging.getLogger(__name__)


@click.command()
@click.option(
    "-i",
    "--input-file",
    required=True,
    help="Filepath for harvested input records to transform",
)
@click.option(
    "-o",
    "--output-file",
    required=True,
    help="Filepath to write output TIMDEX JSON records to",
)
@click.option(
    "-s",
    "--source",
    required=True,
    type=click.Choice(["dspace", "jpal", "whoas", "zenodo"], case_sensitive=False),
    help="Source records were harvested from, must choose from list of options",
)
@click.option(
    "-v", "--verbose", is_flag=True, help="Pass to log at debug level instead of info"
)
def main(source, input_file, output_file, verbose):
    env = os.getenv("WORKSPACE")
    root_logger = logging.getLogger()
    if verbose:
        root_logger.setLevel(logging.DEBUG)
    else:
        root_logger.setLevel(logging.INFO)
    logger.info(
        "Running transmogrifier with env=%s and log level=%s,",
        env,
        logging.getLevelName(logger.getEffectiveLevel()),
    )
    if sentry_dsn := os.getenv("SENTRY_DSN"):
        sentry_sdk.init(sentry_dsn, environment=env)
        logger.info(
            "Sentry DSN found, exceptions will be sent to Sentry with env=%s", env
        )
    logger.info("Running transform for source %s", source)
    if source == "dspace":
        input_records = parse_xml_records(input_file)
        output_records = DspaceMets(
            source, SOURCES[source]["base_url"], SOURCES[source]["name"], input_records
        )
    elif source == "jpal":
        input_records = parse_xml_records(input_file)
        output_records = Datacite(
            source,
            SOURCES[source]["base_url"],
            SOURCES[source]["name"],
            input_records,
        )
    elif source == "whoas":
        input_records = parse_xml_records(input_file)
        output_records = DSpaceDim(
            source,
            SOURCES[source]["base_url"],
            SOURCES[source]["name"],
            input_records,
        )
    elif source == "zenodo":
        input_records = parse_xml_records(input_file)
        output_records = Zenodo(
            source,
            SOURCES[source]["base_url"],
            SOURCES[source]["name"],
            input_records,
        )
    count = write_timdex_records_to_json(output_records, output_file)
    logger.info("Completed transform, total record count: %d", count)
