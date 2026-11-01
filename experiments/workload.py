"""Use a preparation experiment's database to generate and save a BONDI workload."""

from time import monotonic

import yanex
from pymongo import MongoClient

from bondi_demo.workload import generate_workload


def main():
    # Here we fail fast if the experiment does not have the required prepare_db.py dependency
    yanex.assert_dependency("prepare_db.py", "prepare")

    # Load the dataset manifest from the preparation experiment
    manifest = yanex.load_artifact("dataset_manifest.json")
    database, collection = manifest["namespace"].split(".", 1)

    # Generate the workload with our `generate_workload()` helper, defined in src/bondi_demo/workload.py
    started = monotonic()
    with MongoClient(manifest["uri"], serverSelectionTimeoutMS=10000) as client:
        workload, patterns = generate_workload(client[database][collection], **yanex.get_params())

    for i, pattern in enumerate(patterns):
        print(f"> Pattern {i}: {pattern}")

    # We use a custom `saver` function to call the workload's `save` method
    yanex.save_artifact(workload, "workload.jsonl", saver=lambda obj, path: obj.save(path))

    # For the patterns, we serialize them as a list of dictionaries and save as `.jsonl` format.
    yanex.save_artifact([p.to_dict() for p in patterns], "patterns.jsonl")

    # Finally we log some metrics
    yanex.log_metrics(
        {
            "query_count": len(workload),
            "pattern_count": len(patterns),
            "generation_seconds": monotonic() - started,
        }
    )
    print(f"> Saved {len(workload)} queries (based on {len(patterns)} patterns) to workload.jsonl")


if __name__ == "__main__":
    main()
