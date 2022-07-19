import logging
from datetime import timedelta
from time import perf_counter

import click

from transmogrifier.config import (
    SOURCES,
    configure_logger,
    configure_sentry,
    get_transformer,
)
from transmogrifier.helpers import parse_xml_records, write_timdex_records_to_json

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
    type=click.Choice(list(SOURCES.keys()), case_sensitive=False),
    help="Source records were harvested from, must choose from list of options",
)
@click.option(
    "-v", "--verbose", is_flag=True, help="Pass to log at debug level instead of info"
)
def main(source, input_file, output_file, verbose):
    START_TIME = perf_counter()
    root_logger = logging.getLogger()
    logger.info(configure_logger(root_logger, verbose))
    logger.info(configure_sentry())
    logger.info("Running transform for source %s", source)

    input_records = parse_xml_records(input_file)
    transformer_class = get_transformer(source)
    transformer_instance = transformer_class(source, input_records)
    write_timdex_records_to_json(transformer_instance, output_file)
    logger.info(
        (
            "Completed transform, total records processed: %d, transformed records: %d, "
            "skipped records: %d"
        ),
        transformer_instance.processed_record_count,
        transformer_instance.transformed_record_count,
        transformer_instance.skipped_record_count,
    )
    elapsed_time = perf_counter() - START_TIME
    logger.info(
        "Total time to complete transform: %s", str(timedelta(seconds=elapsed_time))
    )
