"""Benchmark one index set against an existing workload experiment."""

from statistics import median

import yanex
from bondi.workload import Workload
from pymongo import MongoClient

from bondi_demo.benchmark import apply_indexes, benchmark_workload


def main():
    # Load queries directly, and database details through the preparation ancestor.
    dependency = yanex.get_dependency("workload")
    if dependency is None:
        raise ValueError("Provide -D workload=<workload-experiment-id>")
    workload = dependency.load_artifact("workload.jsonl", loader=Workload.load)
    manifest = yanex.load_artifact("dataset_manifest.json")
    database, collection = manifest["namespace"].split(".", 1)
    params = yanex.get_params()

    # Index creation is setup, not part of the measured query execution time.
    with MongoClient(manifest["uri"]) as client:
        apply_indexes(client[database][collection], params["indexes"])
    rows = benchmark_workload(
        manifest["uri"],
        workload,
        warmups=params["warmups"],
        repetitions=params["repetitions"],
        timeout_seconds=params["timeout_seconds"],
    )

    # Keep failures visible in the artifact, and never report a failed run as a winner.
    yanex.save_artifact(rows, "query_results.jsonl")
    if any(row["status"] != "success" for row in rows):
        raise RuntimeError("Some queries failed; inspect query_results.jsonl")
    totals = [
        sum(row["elapsed_ms"] for row in rows if row["repetition"] == repetition)
        for repetition in range(params["repetitions"])
    ]
    yanex.save_artifact(totals, "workload_times.json")
    yanex.log_metrics(
        {
            "query_count": len(workload),
            "median_workload_ms": median(totals),
        }
    )
    print(f"> {params['index_set']}: median workload time {median(totals):,.1f} ms")


if __name__ == "__main__":
    main()
