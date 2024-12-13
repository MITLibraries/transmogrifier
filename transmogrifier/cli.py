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
    help="Filepath of input records to transform.  The filename must be in the format "
    "<source>-<YYYY-MM-DD>-<run-type>-extracted-records-to-<action><index[optional]>"
    ".<extension>.  Examples: 'gisogm-2024-03-28-daily-extracted-records-to-index.jsonl' "
    "or 'alma-2023-01-13-full-extracted-records-to-index_17.xml'.",
)
# NOTE: FEATURE FLAG: CLI arg '--output-file' will be removed after v2 work is complete
@click.option(
    "--output-file",
    required=False,
    help="Filepath to write output TIMDEX JSON records to. NOTE: this option will be "
    "removed when output to parquet is finalized.",
)
@click.option(
    "-o",
    "--output-location",
    required=False,
    help="Location of TIMDEX parquet dataset to write to.",
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
    output_location: str,
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
            if output_file is None:
                message = "--output-file must be set when using ETL_VERSION=1"
                raise RuntimeError(message)
            transformer.transform_and_write_output_files(output_file)
        case 2:
            if output_location is None:
                message = "-o / --output-location must be set when using ETL_VERSION=2"
                raise RuntimeError(message)
            transformer.write_to_parquet_dataset(output_location)

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
