"""Check the thin Yanex layer without starting Docker or a real experiment."""

import runpy
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
import yanex

from bondi_demo import data

SCRIPT = Path(__file__).resolve().parents[1] / "experiments" / "prepare_db.py"


@pytest.mark.parametrize("start_docker", [False, True])
@pytest.mark.parametrize("fail", [False, True])
def test_manifest_only_saved_after_success(fail, start_docker):
    client = MagicMock()
    deployment = MagicMock(uri="mongodb://127.0.0.1:27019/", image="mongo:test")
    deployment.name = "bondi-demo"
    with (
        patch.object(yanex, "is_standalone", return_value=False),
        patch.object(
            yanex,
            "get_param",
            side_effect=lambda key, default=None: {
                "start_docker": start_docker,
                "port": 27019,
                "batch_size": 1000,
                "reset": False,
            }.get(key, default),
        ),
        patch.object(yanex, "save_artifact") as save,
        patch.object(yanex, "log_metrics") as metrics,
        patch.object(data, "download_dataset", return_value=Path("cached.jsonl")),
        patch.object(data, "import_dataset", return_value=data.EXPECTED_RECORDS) as importer,
        patch("pymongo.MongoClient", return_value=client) as connect,
        patch("bondi.deployment.deploy_mongodb", return_value=deployment) as deploy,
    ):
        if fail:
            importer.side_effect = ValueError("wrong count")
            with pytest.raises(ValueError, match="wrong count"):
                runpy.run_path(str(SCRIPT), run_name="__main__")
            save.assert_not_called()
            metrics.assert_not_called()
        else:
            runpy.run_path(str(SCRIPT), run_name="__main__")
            manifest, filename = save.call_args.args
            assert filename == "dataset_manifest.json"
            assert manifest["population"] == 189010
            assert manifest["dataset_file"] == "electric_vehicles/train.jsonl"
            assert manifest["deployment_name"] == ("bondi-demo" if start_docker else None)
            assert manifest["deployment_image"] == ("mongo:test" if start_docker else None)
        connect.assert_called_once_with(
            "mongodb://127.0.0.1:27019/", serverSelectionTimeoutMS=10000
        )
        if start_docker:
            deploy.assert_called_once_with("bondi-demo", port=27019)
        else:
            deploy.assert_not_called()
        client.__exit__.assert_called_once()
