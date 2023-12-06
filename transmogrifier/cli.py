import logging
from datetime import timedelta
from time import perf_counter

import click

from transmogrifier.config import SOURCES, configure_logger, configure_sentry
from transmogrifier.sources.transformer import Transformer

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

    transformer = Transformer.load(source, input_file)
    transformer.transform_and_write_output_files(output_file)
    logger.info(
        (
            "Completed transform, total records processed: %d, "
            "transformed records: %d, "
            "skipped records: %d, "
            "deleted records: %d"
        ),
        transformer.processed_record_count,
        transformer.transformed_record_count,
        transformer.skipped_record_count,
        len(transformer.deleted_records),
    )
    elapsed_time = perf_counter() - START_TIME
    logger.info(
        "Total time to complete transform: %s", str(timedelta(seconds=elapsed_time))
    )
