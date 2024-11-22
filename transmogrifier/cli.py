import logging
from datetime import timedelta
from time import perf_counter

import click

from transmogrifier.config import (
    SOURCES,
    configure_logger,
    configure_sentry,
    get_etl_version,
)
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
    "-r",
    "--run-id",
    required=False,
    help="Identifier for Transmogrifier run.  This can be used to group transformed "
    "records produced by Transmogrifier, even if they span multiple CLI invocations.  "
    "If a value is not provided a UUID will be minted and used.",
)
@click.option(
    "-v", "--verbose", is_flag=True, help="Pass to log at debug level instead of info"
)
def main(
    source: str,
    input_file: str,
    output_file: str,
    run_id: str,
    verbose: bool,  # noqa: FBT001
) -> None:
    start_time = perf_counter()
    root_logger = logging.getLogger()
    logger.info(configure_logger(root_logger, verbose))
    logger.info(configure_sentry())
    logger.info("Running transform for source %s", source)

    transformer = Transformer.load(source, input_file, run_id=run_id)

    # NOTE: FEATURE FLAG: branching logic will be removed after v2 work is complete
    etl_version = get_etl_version()
    match etl_version:
        case 1:
            transformer.transform_and_write_output_files(output_file)
        case 2:
            transformer.write_to_parquet_dataset(output_file)

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

    elapsed_time = perf_counter() - start_time
    logger.info(
        "Total time to complete transform: %s", str(timedelta(seconds=elapsed_time))
    )
