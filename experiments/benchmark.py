"""Benchmark one index set against an existing workload experiment."""

from statistics import median

import yanex
from bondi.workload import Workload
from pymongo import MongoClient

from bondi_demo.benchmark import apply_indexes, benchmark_workload


def main():
    # Here we fail fast if the experiment does not have the required workload dependency
    yanex.assert_dependency("workload.py", "workload")

    # Next we load the workload and dataset manifest
    # Yanex will search through the dependency chain for the required artifacts
    workload = yanex.load_artifact("workload.jsonl", loader=Workload.load)
    manifest = yanex.load_artifact(
        "dataset_manifest.json"
    )  # loaded from the prepare_db.py experiment

    database, collection = manifest["namespace"].split(".", 1)

    # Load the parameters from the config file
    params = yanex.get_params()

    # Ensure an index set was provided
    if "index_set" not in params:
        raise ValueError(
            "Provide index_set, one of `baseline`, `single`, or `compound`. See configs/benchmark.yaml"
        )

    # Get correct index set from config based on `index_set` parameter
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

    # log metrics for the workload
    yanex.log_metrics(
        {
            "query_count": len(workload),
            "workloads_ms": totals,  # list of workload times for each repetition
            "median_workload_ms": median(totals),  # median of workload times
        }
    )
    print(f"> {params['index_set']}: median workload time {median(totals):,.1f} ms")


if __name__ == "__main__":
    main()
