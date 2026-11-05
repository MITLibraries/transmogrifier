import os
from concurrent.futures.process import BrokenProcessPool

import pytest

from transmogrifier import parallel
from transmogrifier.exceptions import CriticalError
from transmogrifier.parallel import iter_transformed_records
from transmogrifier.sources.transformer import Transformer
from transmogrifier.sources.xml.datacite import Datacite
from transmogrifier.sources.xmltransformer import XMLTransformer

COUNT_ATTRIBUTES = (
    "processed_record_count",
    "transformed_record_count",
    "skipped_record_count",
    "error_record_count",
    "deleted_records",
)


class CriticalErrorDatacite(Datacite):
    """Module level, so worker processes can import it."""

    def get_timdex_record_id(self, _source_record):
        raise CriticalError("Catastrophic failure in a worker!")


class DyingWorkerDatacite(Datacite):
    """Module level, so worker processes can import it."""

    def get_timdex_record_id(self, _source_record):
        os._exit(1)


@pytest.fixture
def load_transformer(source_input_file, run_id):
    def _load():
        return Transformer.load(
            "jpal",
            source_input_file,
            run_id=run_id,
            run_timestamp="2024-06-03T15:30:45",
        )

    return _load


@pytest.mark.parametrize(
    ("chunk_size", "max_pending_chunks_per_worker"),
    [(1, 1), (2, 1), (100, 4)],
)
def test_iter_transformed_records_matches_single_process(
    monkeypatch, load_transformer, chunk_size, max_pending_chunks_per_worker
):
    monkeypatch.setattr(parallel, "WORKER_CHUNK_SIZE", chunk_size)
    monkeypatch.setattr(
        parallel, "WORKER_MAX_PENDING_CHUNKS_PER_WORKER", max_pending_chunks_per_worker
    )
    single_process = load_transformer()
    single_process_records = list(single_process)

    with_workers = load_transformer()
    with_workers_records = list(iter_transformed_records(with_workers, workers=2))

    assert with_workers_records == single_process_records
    assert len(with_workers.deleted_records) == 1
    for attribute in COUNT_ATTRIBUTES:
        assert getattr(with_workers, attribute) == getattr(single_process, attribute)


def test_iter_transformed_records_critical_error_stops_run(source_input_file):
    transformer = CriticalErrorDatacite(
        "jpal",
        XMLTransformer.read_source_file(source_input_file),
        source_file=source_input_file,
    )
    with pytest.raises(CriticalError, match="Catastrophic failure in a worker!"):
        list(iter_transformed_records(transformer, workers=2))


def test_iter_transformed_records_worker_process_death_stops_run(source_input_file):
    transformer = DyingWorkerDatacite(
        "jpal",
        XMLTransformer.read_source_file(source_input_file),
        source_file=source_input_file,
    )
    with pytest.raises(BrokenProcessPool):
        list(iter_transformed_records(transformer, workers=2))


def test_transformer_iterates_provided_transformed_records(load_transformer):
    transformer = load_transformer()
    provided_records = iter(["a", "b"])
    transformer._transformed_records = provided_records  # noqa: SLF001

    assert iter(transformer) is provided_records
    assert list(transformer) == ["a", "b"]


def test_transformer_iterates_itself_by_default(load_transformer):
    transformer = load_transformer()
    assert iter(transformer) is transformer
