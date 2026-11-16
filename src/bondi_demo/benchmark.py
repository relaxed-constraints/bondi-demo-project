"""Apply an index set and measure a saved workload, independently of Yanex."""

from bondi import IndexSet, MongoConnection, create_indexes
from bondi.mongodb import MongoExecutor
from bondi.workload import Workload


def apply_indexes(uri: str, *, database: str, indexes: IndexSet) -> dict[str, list[str]]:
    """Replace the selected collections' secondary indexes and return created names.

    IndexSet keys are collection names. BONDI replaces secondary indexes, preserves
    MongoDB's built-in _id_ index and waits for initial builds. Empty collection lists
    clear secondary indexes. Run scenarios sequentially on a dedicated demo database;
    replacement is non-atomic and affects every user of those collections.
    """
    return create_indexes(MongoConnection(uri), database=database, indexes=indexes, replace=True)


def benchmark_workload(
    uri: str,
    workload: Workload,
    *,
    warmups: int = 1,
    repetitions: int = 3,
    timeout_seconds: float = 60,
    verbose: bool = False,
) -> list[dict]:
    """Return per-query measurements, fully consuming results without retaining them.

    Timings are client-observed milliseconds, including fetching result rows.
    Warm-up passes are excluded; measured failures are retained for inspection.
    """
    if warmups < 0 or repetitions < 1:
        raise ValueError("warmups must be nonnegative and repetitions must be positive")
    rows = []
    with MongoExecutor.from_uri(
        uri,
        concurrency=1,
        continue_on_error=True,
        timeout_seconds=timeout_seconds,
    ) as executor:
        for w in range(warmups):
            if verbose:
                print(f"> Executing warm-up pass {w + 1}/{warmups}")
            results = executor.run_workload(workload)
            if any(result.error is not None for result in results):
                raise RuntimeError("Warm-up query failed; check the workload and database")
        for repetition in range(repetitions):
            if verbose:
                print(f"> Executing repetition {repetition + 1}/{repetitions}")

            results = executor.run_workload(workload)
            for query_id, (entry, result) in enumerate(zip(workload, results)):
                rows.append(
                    {
                        "repetition": repetition,
                        "query_id": query_id,
                        "pattern_id": entry.pattern_id,
                        "elapsed_ms": result.elapsed_ms,
                        "row_count": result.row_count,
                        "status": result.status,
                        "error": str(result.error) if result.error else None,
                    }
                )
    return rows
