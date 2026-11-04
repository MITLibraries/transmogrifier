"""Transform records with a pool of worker processes.

Transforming records can be CPU heavy, and a Python process effectively uses one CPU core
at a time.  When the CLI is run with more than one worker, this module spreads that work
across multiple processes, and keeps multiprocessing concerns out of the Transformer
classes.

Transformers are used almost untouched:
    - Each worker process has its own transformer, which iterates over source records as
    usual, but is given one chunk of them at a time.
    - The main process transformer reads the source records and writes the output as
    usual, but its __iter__() returns the records coming back from the workers, by way of
    _transformed_records, instead of transforming them itself.
"""

from __future__ import annotations

import itertools
import logging
import multiprocessing
from collections import deque
from concurrent.futures import ProcessPoolExecutor
from typing import TYPE_CHECKING

from transmogrifier.config import configure_logger, configure_sentry

if TYPE_CHECKING:
    from collections.abc import Iterable, Iterator
    from concurrent.futures import Future

    from bs4 import Tag
    from timdex_dataset_api import DatasetRecord

    from transmogrifier.sources.transformer import JSON, Transformer

logger = logging.getLogger(__name__)

WORKER_CHUNK_SIZE = 100
WORKER_MAX_PENDING_CHUNKS_PER_WORKER = 4

# set once per worker process by _init_worker(), and used by _transform_chunk()
_worker_transformer: Transformer | None = None


def iter_transformed_records(
    transformer: Transformer, workers: int
) -> Iterator[DatasetRecord]:
    """Yield DatasetRecords for a transformer's source records, using worker processes.

    The main process reads chunks of the transformer's source records and sends them to
    workers.  Each worker has its own transformer that iterates over one chunk at a time,
    as it would for a whole run, and returns the resulting DatasetRecords.

    Records are yielded in input order, and only a limited number of chunks are in flight
    at a time.  Chunks are only read as records are consumed, which limits memory use.

    The record counts and deleted records of the passed transformer are updated as records
    are yielded.  A CriticalError in any worker, or a worker process dying, stops the run.

    Args:
        transformer: The main process transformer, whose source records are read.
        workers: The number of worker processes to use.
    """
    logger.info(f"Transforming records with {workers} worker processes")
    # "spawn" starts each worker as a fresh Python process, instead of a copy of this one,
    # so each worker runs _init_worker() once at startup to set itself up
    executor = ProcessPoolExecutor(
        max_workers=workers,
        mp_context=multiprocessing.get_context("spawn"),
        initializer=_init_worker,
        initargs=(
            type(transformer),
            transformer.source,
            transformer.exclusion_list_path,
            transformer.run_data,
            logging.getLogger().getEffectiveLevel() == logging.DEBUG,
        ),
    )

    # the upper limit of chunks in flight, which are chunks sent to workers but not yet
    # yielded here; this keeps a large input from piling up in memory
    max_pending_chunks = workers * WORKER_MAX_PENDING_CHUNKS_PER_WORKER

    pending: deque[Future[list[DatasetRecord]]] = deque()
    start_offset = 0
    try:
        for chunk in itertools.batched(
            transformer.source_records, WORKER_CHUNK_SIZE, strict=False
        ):
            pending.append(executor.submit(_transform_chunk, start_offset, list(chunk)))
            start_offset += len(chunk)

            # at the limit, stop reading source records until the oldest chunk is done
            #   - workers can finish chunks in any order, but always taking the oldest
            #   chunk means records are yielded in input order
            #   - result() blocks until the chunk is done, and re-raises any exception
            #   from the worker
            if len(pending) >= max_pending_chunks:
                yield from _tally_run_counts(transformer, pending.popleft().result())

        while pending:
            yield from _tally_run_counts(transformer, pending.popleft().result())
    finally:
        executor.shutdown(wait=True, cancel_futures=True)


def _tally_run_counts(
    transformer: Transformer, records: Iterable[DatasetRecord]
) -> Iterator[DatasetRecord]:
    """Update a transformer's record counts and deleted records, and yield each record."""
    for record in records:
        transformer.processed_record_count += 1
        match record.action:
            case "index":
                transformer.transformed_record_count += 1
            case "delete":
                transformer.deleted_records.append(record.timdex_record_id)
            case "skip":
                transformer.skipped_record_count += 1
            case "error":
                transformer.error_record_count += 1
        yield record


def _init_worker(
    transformer_class: type[Transformer],
    source: str,
    exclusion_list_path: str | None,
    run_data: dict,
    verbose: bool,  # noqa: FBT001
) -> None:
    """Configure this worker process and build its transformer.

    The transformer starts with no source records, iter(()), because _transform_chunk()
    sets them for each chunk.
    """
    global _worker_transformer  # noqa: PLW0603
    configure_logger(logging.getLogger(), verbose=verbose)
    configure_sentry()
    _worker_transformer = transformer_class(
        source, iter(()), exclusion_list_path=exclusion_list_path
    )
    _worker_transformer.run_data = run_data


def _transform_chunk(
    start_offset: int, source_records: list[bytes | dict[str, JSON] | Tag]
) -> list[DatasetRecord]:
    """Transform one chunk of source records in a worker process.

    Setting the processed record count means each record gets its position in the whole
    run as its run_record_offset.  The worker's other counts and deleted records are not
    used; the main process tallies them from the returned records.

    Args:
        start_offset: The run_record_offset of the first record in the chunk.
        source_records: The chunk of source records, in run order.
    """
    if _worker_transformer is None:
        raise RuntimeError("Worker transformer was not initialized")
    _worker_transformer.source_records = iter(source_records)
    _worker_transformer.processed_record_count = start_offset
    return list(_worker_transformer)
