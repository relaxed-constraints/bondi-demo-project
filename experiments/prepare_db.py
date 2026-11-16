import yanex
from bondi.deployment import deploy_mongodb

from bondi_demo import data


def main():

    # load yanex parameters
    start_docker = yanex.get_param("start_docker", True)
    port = yanex.get_param("port", 27017)
    batch_size = yanex.get_param("batch_size", 1000)
    reset = yanex.get_param("reset", True)

    # BONDI owns Docker setup and readiness; keep it running for later experiments.
    uri = f"mongodb://127.0.0.1:{port}/"
    deployment = None
    if start_docker:
        deployment = deploy_mongodb("bondi-demo", port=port)
        print(f"> Deployed MongoDB at {deployment.uri}")
        uri = deployment.uri

    # BONDI downloads and loads the source; the helper handles this demo's
    # reset and failed-import cleanup policy.
    count = data.load_dataset(uri, batch_size=batch_size, reset=reset)
    print(f"> Imported {count} records into {data.DATABASE}.{data.COLLECTION}")

    manifest = {
        "dataset_repo": data.DATASET_REPO,
        "dataset_file": data.DATASET_FILE,
        "dataset_config": data.DATASET_CONFIG,
        "dataset_split": data.DATASET_SPLIT,
        "namespace": f"{data.DATABASE}.{data.COLLECTION}",
        "population": count,
        "uri": uri,
        "deployment_name": deployment.name if deployment else None,
        "deployment_image": deployment.image if deployment else None,
    }

    # Store yanex artifact and log metrics
    yanex.save_artifact(manifest, "dataset_manifest.json")
    yanex.log_metrics({"imported_records": count})


if __name__ == "__main__":
    main()
