"""Yanex orchestration: configuration → reusable functions → tracked artifacts."""

from pathlib import Path
from time import monotonic

import yanex
from pymongo import MongoClient

from bondi_demo import data


def main():
    if yanex.is_standalone():
        raise RuntimeError(
            "Use yanex run experiments/prepare_db.py -c experiments/configs/prepare.yaml"
        )
    params = yanex.get_params()
    started = monotonic()

    # Keep generated Docker assets out of Git; paths do not depend on shell cwd.
    project = Path(__file__).resolve().parents[1]
    compose_path = project / "data" / "compose.yaml"
    if params["start_docker"]:
        data.start_database(compose_path)

    # Download/check before replacing any existing collection.
    path = data.download_dataset()
    uri = "mongodb://127.0.0.1:27017/"
    with MongoClient(uri, serverSelectionTimeoutMS=10000) as client:
        client.admin.command("ping")
        count = data.import_dataset(
            path,
            client[data.DATABASE],
            batch_size=params["batch_size"],
            reset=params["reset"],
        )

    # The manifest records data identity, not a machine-specific cache path.
    manifest = {
        "dataset_repo": data.DATASET_REPO,
        "dataset_revision": data.DATASET_REVISION,
        "dataset_file": data.DATASET_FILE,
        "sha256": data.DATASET_SHA256,
        "namespace": f"{data.DATABASE}.{data.COLLECTION}",
        "population": count,
        "uri": uri,
        "bondi_compose_revision": data.BONDI_REVISION if params["start_docker"] else None,
    }
    yanex.save_artifact(manifest, "dataset_manifest.json")
    yanex.log_metrics({"imported_records": count, "prepare_seconds": monotonic() - started})
    print(f"Ready: {manifest['namespace']} ({count:,} documents)")


if __name__ == "__main__":
    main()
