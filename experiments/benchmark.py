"""Benchmark one index set against an existing workload experiment."""

from statistics import median

import yanex
from bondi.workload import Workload
from pymongo import MongoClient

from bondi_demo.benchmark import apply_indexes, benchmark_workload


def main():
    # Load queries directly, and database details through the preparation ancestor.
    yanex.assert_dependency("workload.py", "workload")
    dependency = yanex.get_dependency("workload")

    workload = dependency.load_artifact("workload.jsonl", loader=Workload.load)
    manifest = yanex.load_artifact("dataset_manifest.json")
    database, collection = manifest["namespace"].split(".", 1)
    params = yanex.get_params()

    # Ensure an index set was provided
    if "index_set" not in params:
        raise ValueError(
            "Provide index_set, one of `baseline`, `single`, or `compound`. See configs/benchmark.yaml"
        )

    # Get correct index set from config based on `index_set` parameter
    # String `baseline` in yaml maps to None, replacing with string "none" here
    indexes = params["indexes"][params["index_set"]]

    # Index creation is setup, not part of the measured query execution time.
    with MongoClient(manifest["uri"]) as client:
        apply_indexes(client[database][collection], indexes)
        print(f"> Applied indexes for index set '{params['index_set']}'")
        for i, index in enumerate(indexes):
            print(f"  {i}. {index}")

    rows = benchmark_workload(
        manifest["uri"],
        workload,
        warmups=params["warmups"],
        repetitions=params["repetitions"],
        timeout_seconds=params["timeout_seconds"],
        verbose=True,
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
