"""Use a preparation experiment's database to generate and save a BONDI workload."""

from time import monotonic

import yanex
from pymongo import MongoClient

from bondi_demo.workload import generate_workload


def main():
    # The named dependency supplies the database location, not a new database copy.
    prepare = yanex.get_dependency("prepare")
    if prepare is None:
        raise ValueError("Provide the preparation experiment with -D prepare=<experiment-id>")
    manifest = prepare.load_artifact("dataset_manifest.json")
    database, collection = manifest["namespace"].split(".", 1)

    # Ordinary Python code does the work; Yanex supplies configuration and tracking.
    started = monotonic()
    with MongoClient(manifest["uri"], serverSelectionTimeoutMS=10000) as client:
        workload = generate_workload(client[database][collection], **yanex.get_params())

    # BONDI's serializer preserves query types, options and pattern IDs.
    yanex.save_artifact(workload, "workload.jsonl", saver=lambda obj, path: obj.save(path))
    yanex.log_metrics(
        {
            "query_count": len(workload),
            "generation_seconds": monotonic() - started,
        }
    )
    print(f"> Saved {len(workload)} queries to workload.jsonl")


if __name__ == "__main__":
    main()
