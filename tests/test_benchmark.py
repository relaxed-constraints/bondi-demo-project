"""Test index replacement and the measurement boundary without a database."""

import runpy
from pathlib import Path
from unittest.mock import MagicMock, call, patch

import pytest
import yanex
from bondi import FieldIndex, IndexSet
from bondi.execution import ExecutionResult
from bondi.mongodb import MongoCollectionRef, MongoFindQuery
from bondi.workload import Workload, WorkloadEntry

from bondi_demo.benchmark import apply_indexes, benchmark_workload


@pytest.fixture
def workload():
    return Workload(
        [
            WorkloadEntry(
                MongoFindQuery(MongoCollectionRef("demo", "cars"), {"Make": "FORD"}), pattern_id=0
            )
        ]
    )


def test_index_replacement_preserves_compound_order():
    indexes = IndexSet.from_dict({"cars": [{"keys": [["Make", 1], ["Model Year", -1]]}]})
    with patch(
        "bondi_demo.benchmark.create_indexes", return_value={"cars": ["compound"]}
    ) as create:
        assert apply_indexes("mongodb://localhost", database="demo", indexes=indexes) == {
            "cars": ["compound"]
        }
        assert create.call_args.kwargs["indexes"]["cars"][0].keys == (
            ("Make", 1),
            ("Model Year", -1),
        )
        assert create.call_args.kwargs["database"] == "demo"
        assert create.call_args.kwargs["replace"] is True
        assert create.call_args.args[0].uri == "mongodb://localhost"

        baseline = IndexSet({"cars": []})
        apply_indexes("mongodb://localhost", database="demo", indexes=baseline)
        assert create.call_args.kwargs["indexes"]["cars"] == []
        assert create.call_args.kwargs["replace"] is True


def test_index_failure_propagates():
    failure = RuntimeError("index replacement failed")
    with patch("bondi_demo.benchmark.create_indexes", side_effect=failure):
        with pytest.raises(RuntimeError) as caught:
            apply_indexes("mongodb://localhost", database="demo", indexes=IndexSet({"cars": []}))
    assert caught.value is failure


def test_config_index_sets_roundtrip(tmp_path):
    import yaml

    root = Path(__file__).resolve().parents[1]
    config = yaml.safe_load((root / "experiments/configs/benchmark.yaml").read_text())
    expected = {"baseline": 0, "single": 5, "compound": 4}
    for name, count in expected.items():
        indexes = IndexSet.from_dict({"cars": config["indexes"][name]})
        indexes.save(tmp_path / "indexes.json")
        assert IndexSet.load(tmp_path / "indexes.json").to_dict() == indexes.to_dict()
        assert len(indexes["cars"]) == count
        assert all(type(index) is FieldIndex for index in indexes["cars"])
    compound = IndexSet.from_dict({"cars": config["indexes"]["compound"]})
    assert compound["cars"][0].keys == (("Make", 1), ("Model Year", 1))


def test_warmup_excluded_and_failures_retained(workload):
    executor = MagicMock()
    executor.run_workload.side_effect = [
        [ExecutionResult(100, row_count=2)],
        [ExecutionResult(5, row_count=2)],
        [ExecutionResult(10, error=TimeoutError("too slow"))],
    ]
    with patch("bondi_demo.benchmark.MongoExecutor.from_uri") as connect:
        connect.return_value.__enter__.return_value = executor
        rows = benchmark_workload("mongodb://localhost", workload, repetitions=2)
    assert [row["elapsed_ms"] for row in rows] == [5, 10]
    assert [row["status"] for row in rows] == ["success", "timeout"]
    assert rows[1]["error"] == "too slow"
    assert rows[0]["pattern_id"] == 0
    assert connect.call_args.kwargs["concurrency"] == 1
    connect.return_value.__exit__.assert_called_once()


@pytest.mark.parametrize("failed", [False, True])
def test_experiment_saves_measurements_before_reporting(workload, failed, tmp_path):
    dependency = MagicMock()
    dependency.load_artifact.return_value = workload
    rows = [{"repetition": 0, "elapsed_ms": 5, "status": "error" if failed else "success"}]
    with (
        patch.object(yanex, "get_dependency", return_value=dependency),
        patch.object(
            yanex,
            "load_artifact",
            return_value={
                "uri": "mongodb://localhost",
                "namespace": "demo.cars",
            },
        ),
        patch.object(
            yanex,
            "get_params",
            return_value={
                "indexes": {"baseline": []},
                "warmups": 0,
                "repetitions": 1,
                "timeout_seconds": 60,
                "index_set": "baseline",
            },
        ),
        patch.object(yanex, "save_artifact") as save,
        patch.object(yanex, "log_metrics") as log,
        patch("bondi_demo.benchmark.apply_indexes", return_value={"cars": []}) as apply,
        patch("bondi_demo.benchmark.benchmark_workload", return_value=rows),
    ):
        script = Path(__file__).resolve().parents[1] / "experiments/benchmark.py"
        if failed:
            with pytest.raises(RuntimeError, match="Some queries failed"):
                runpy.run_path(str(script), run_name="__main__")
            log.assert_not_called()
        else:
            runpy.run_path(str(script), run_name="__main__")
            assert log.call_args.args[0]["median_workload_ms"] == 5
        saved_indexes = save.call_args_list[0]
        assert saved_indexes.args[1] == "indexes.json"
        saved_indexes.kwargs["saver"](saved_indexes.args[0], tmp_path / "indexes.json")
        assert IndexSet.load(tmp_path / "indexes.json").to_dict() == {"cars": []}
        assert save.call_args_list[1] == call({"cars": []}, "index_names.json")
        assert save.call_args_list[2] == call(rows, "query_results.jsonl")
        assert apply.call_args.kwargs["database"] == "demo"
