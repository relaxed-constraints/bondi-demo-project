"""Check the thin Yanex layer without starting Docker or a real experiment."""

import runpy
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
import yanex

from bondi_demo import data

SCRIPT = Path(__file__).resolve().parents[1] / "experiments" / "prepare_db.py"


@pytest.mark.parametrize("fail", [False, True])
def test_manifest_only_saved_after_success(fail):
    client = MagicMock()
    with (
        patch.object(yanex, "is_standalone", return_value=False),
        patch.object(
            yanex,
            "get_params",
            return_value={
                "start_docker": False,
                "batch_size": 1000,
                "reset": False,
            },
        ),
        patch.object(yanex, "save_artifact") as save,
        patch.object(yanex, "log_metrics") as metrics,
        patch.object(data, "download_dataset", return_value=Path("cached.jsonl")),
        patch.object(data, "import_dataset", return_value=data.EXPECTED_RECORDS) as importer,
        patch("pymongo.MongoClient", return_value=client),
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
            assert manifest["sha256"] == data.DATASET_SHA256
        client.__exit__.assert_called_once()
