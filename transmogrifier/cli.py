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
    "-id",
    "--input-dataset",
    required=False,
    help="Location of TIMDEX parquet dataset with source records used as input.",
)
@click.option(
    "-ip",
    "--input-parquet",
    required=False,
    help=(
        "Location of a parquet file, or directory of parquet files, with source "
        "records used as input."
    ),
)
@click.option(
    "-of",
    "--output-file",
    required=False,
    help=(
        "Filepath (local or S3) of a JSONLines file to write transformed records to, "
        "one per line.  Only records with action 'index' are written."
    ),
)
@click.option(
    "-o",
    "--output-dataset",
    required=False,
    help="Location of TIMDEX dataset to write to.",
)
@click.option(
    "-op",
    "--output-parquet",
    required=False,
    help=(
        "Location of a directory to write parquet files to.  Files have the TIMDEX "
        "records schema, but no dataset partitioning or metadata."
    ),
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
    input_file: str | None,
    input_dataset: str | None,
    input_parquet: str | None,
    output_file: str | None,
    output_dataset: str | None,
    output_parquet: str | None,
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

    _validate_options(
        inputs={
            "--input-file": input_file,
            "--input-dataset": input_dataset,
            "--input-parquet": input_parquet,
        },
        outputs={
            "--output-file": output_file,
            "--output-dataset": output_dataset,
            "--output-parquet": output_parquet,
        },
    )

    transformer = Transformer.load(
        source,
        source_file=input_file,
        source_dataset=input_dataset,
        source_parquet=input_parquet,
        exclusion_list_path=exclusion_list_path,
        run_id=run_id,
        run_timestamp=run_timestamp,
    )
    if output_file:
        transformer.write_to_file(output_file)
    elif output_dataset:
        transformer.write_to_timdex_dataset(output_dataset)
    elif output_parquet:
        transformer.write_to_parquet_files(output_parquet)

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


def _validate_options(
    inputs: dict[str, str | None],
    outputs: dict[str, str | None],
) -> None:
    """Ensure exactly one input option and exactly one output option are set."""
    for kind, options in (("input", inputs), ("output", outputs)):
        if len([value for value in options.values() if value]) != 1:
            raise click.UsageError(
                f"Exactly one {kind} option is required: {' or '.join(options)}"
            )
