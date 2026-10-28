"""Yanex orchestration: configuration → reusable functions → tracked artifacts."""

from time import monotonic

import yanex
from bondi.deployment import deploy_mongodb
from pymongo import MongoClient

from bondi_demo import data


def main():
    if yanex.is_standalone():
        raise RuntimeError(
            "Use yanex run experiments/prepare_db.py -c experiments/configs/prepare.yaml"
        )
    params = yanex.get_params()
    started = monotonic()

    # BONDI owns Docker setup and readiness; keep it running for later experiments.
    uri = f"mongodb://127.0.0.1:{params['port']}/"
    deployment = None
    if params["start_docker"]:
        deployment = deploy_mongodb("bondi-demo", port=params["port"])
        uri = deployment.uri

    # Download/check before replacing any existing collection.
    path = data.download_dataset()
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
        "deployment_name": deployment.name if deployment else None,
        "deployment_image": deployment.image if deployment else None,
    }
    yanex.save_artifact(manifest, "dataset_manifest.json")
    yanex.log_metrics({"imported_records": count, "prepare_seconds": monotonic() - started})
    print(f"Ready: {manifest['namespace']} ({count:,} documents)")


if __name__ == "__main__":
    main()
