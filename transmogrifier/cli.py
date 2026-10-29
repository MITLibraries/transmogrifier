import logging
from datetime import timedelta
from time import perf_counter

import click

from transmogrifier.config import SOURCES, configure_logger, configure_sentry
from transmogrifier.sources.transformer import Transformer

logger = logging.getLogger(__name__)


@click.command()
@click.option(
    "-s",
    "--source",
    required=True,
    type=click.Choice(list(SOURCES.keys()), case_sensitive=False),
    help="Source records were harvested from, must choose from list of options",
)
@click.option(
    "-i",
    "--input-file",
    required=False,
    help=(
        "Filepath of input records to transform.  The filename must be in the format "
        "<source>-<YYYY-MM-DD>-<run-type>-extracted-records-to-<action><index[optional]>"
        ".<extension>.  Examples: 'gisogm-2024-03-28-daily-extracted-records-to-index.jsonl' "  # noqa: E501
        "or 'alma-2023-01-13-full-extracted-records-to-index_17.xml'."
    ),
)
@click.option(
    "-d",
    "--dataset",
    required=False,
    help="Location of TIMDEX parquet dataset with source records to transform.",
)
@click.option(
    "-o",
    "--output-location",
    required=False,
    help="Location of TIMDEX dataset to write to.",
)
@click.option(
    "-e",
    "--exclusion-list-path",
    required=False,
    help="S3 or local path to exclusion list.",
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
    "-t",
    "--run-timestamp",
    required=False,
    help="Run timestamp for the ETL run this Transmogrifier run is part of.  It is "
    "possible for the TIMDEX StepFunction to invoke Transmogrifier multiple times, this "
    "allows a single run_timestamp to be associated with all outputs for single run_id.",
)
@click.option(
    "-v", "--verbose", is_flag=True, help="Pass to log at debug level instead of info"
)
def main(
    source: str,
    input_file: str,
    dataset: str,
    output_location: str,
    exclusion_list_path: str,
    run_id: str,
    run_timestamp: str,
    verbose: bool,  # noqa: FBT001
) -> None:
    start_time = perf_counter()
    root_logger = logging.getLogger()
    logger.info(configure_logger(root_logger, verbose=verbose))
    logger.info(configure_sentry())
    logger.info("Running transform for source %s", source)

    _validate_input_options(input_file, dataset, output_location)

    # default the output location to the input dataset after validation
    output_location = output_location or dataset

    transformer = Transformer.load(
        source,
        source_file=input_file,
        source_dataset=dataset,
        exclusion_list_path=exclusion_list_path,
        run_id=run_id,
        run_timestamp=run_timestamp,
    )
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


def _validate_input_options(
    input_file: str | None = None,
    dataset: str | None = None,
    output_location: str | None = None,
) -> None:
    if (input_file and dataset) or (not input_file and not dataset):
        raise click.UsageError(
            "Exactly one input source is required: --input-file or --dataset"
        )
    if input_file and not output_location:
        raise click.UsageError("--input-file must be used with --output-location")
    if (dataset and output_location) and (dataset != output_location):
        logger.warning(
            "Transformed records will be written to a different TIMDEX dataset: "
            f"{output_location}"
        )
