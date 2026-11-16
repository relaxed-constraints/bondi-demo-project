"""Apply an index set and measure a saved workload, independently of Yanex."""

from bondi import FieldIndex, IndexSet, MongoConnection
from bondi.mongodb import MongoExecutor, MongoIndex, create_indexes
from bondi.workload import Workload
from pymongo import MongoClient


def apply_indexes(uri: str, *, database: str, indexes: IndexSet) -> dict[str, list[str]]:
    """Replace the selected collections' secondary indexes and return created names.

    IndexSet keys are collection names. The demo owns the destructive reset;
    BONDI creates the definitions and waits for their initial builds. MongoDB
    keeps its built-in _id_ index. Run scenarios sequentially on a dedicated
    demo database because index changes affect all users of these collections.
    """
    indexes.validate()
    for definitions in indexes.values():
        names = set()
        for index in definitions:
            if not isinstance(index, (FieldIndex, MongoIndex)):
                raise TypeError("The MongoDB benchmark requires FieldIndex or MongoIndex")
            if index.resolved_name in names:
                raise ValueError("Duplicate index name in benchmark configuration")
            names.add(index.resolved_name)

    # Index replacement belongs to this experiment, not BONDI's creation API.
    with MongoClient(uri) as client:
        for collection in indexes:
            client[database][collection].drop_indexes()
    return create_indexes(MongoConnection(uri), database=database, indexes=indexes)


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
