"""Exercise real BONDI generation and serialization using a tiny sample."""

import runpy
from collections import Counter
from pathlib import Path
from unittest.mock import MagicMock, patch

import yanex
from bondi.workload import Workload

from bondi_demo.workload import generate_workload


def test_generation_and_experiment_artifact(tmp_path):
    collection = MagicMock()
    collection.name = "electric_vehicles"
    collection.database.name = "bondi_demo"
    collection.aggregate.return_value.__enter__.return_value = [
        {"Make": "TESLA", "Model Year": 2020, "Range": 300},
        {"Make": "FORD", "Model Year": 2023, "Range": 200},
        {"Make": "BMW", "Model Year": 2021, "Range": 250},
    ]
    workload = generate_workload(collection)
    assert Counter(entry.pattern_id for entry in workload) == dict.fromkeys(range(5), 20)
    assert all(1 <= len(entry.query.filter) <= 3 for entry in workload)
    collection.aggregate.assert_called_once_with([{"$sample": {"size": 1000}}])

    prepare = MagicMock()
    prepare.load_artifact.return_value = {
        "uri": "mongodb://localhost:27019/",
        "namespace": "bondi_demo.electric_vehicles",
    }
    client = MagicMock()
    artifact = tmp_path / "workload.jsonl"

    def save(obj, filename, *, saver):
        assert filename == artifact.name
        saver(obj, artifact)

    with (
        patch.object(yanex, "get_dependency", return_value=prepare) as dependency,
        patch.object(yanex, "get_params", return_value={"seed": 42}),
        patch.object(yanex, "save_artifact", side_effect=save),
        patch.object(yanex, "log_metrics") as metrics,
        patch("pymongo.MongoClient", return_value=client) as connect,
        patch("bondi_demo.workload.generate_workload", return_value=workload) as generate,
    ):
        script = Path(__file__).resolve().parents[1] / "experiments/workload.py"
        runpy.run_path(str(script), run_name="__main__")

    dependency.assert_called_once_with("prepare")
    prepare.load_artifact.assert_called_once_with("dataset_manifest.json")
    connect.assert_called_once_with("mongodb://localhost:27019/", serverSelectionTimeoutMS=10000)
    generate.assert_called_once_with(
        client.__enter__.return_value["bondi_demo"]["electric_vehicles"],
        seed=42,
    )
    assert metrics.call_args.args[0]["query_count"] == 100
    restored = Workload.load(artifact)
    assert [entry.query.to_json() for entry in restored] == [
        entry.query.to_json() for entry in workload
    ]
    assert [entry.pattern_id for entry in restored] == [entry.pattern_id for entry in workload]
