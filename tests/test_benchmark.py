"""Test index replacement and the measurement boundary without a database."""

import runpy
from pathlib import Path
from unittest.mock import MagicMock, call, patch

import pytest
import yanex
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
    collection = MagicMock()
    apply_indexes(collection, [[["Make", 1], ["Model Year", -1]]])
    assert collection.method_calls == [
        call.drop_indexes(),
        call.create_index([("Make", 1), ("Model Year", -1)]),
    ]
    collection.reset_mock()
    apply_indexes(collection, [])
    collection.drop_indexes.assert_called_once()
    collection.create_index.assert_not_called()


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
def test_experiment_saves_measurements_before_reporting(workload, failed):
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
        patch("pymongo.MongoClient"),
        patch("bondi_demo.benchmark.apply_indexes"),
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
        assert save.call_args_list[0] == call(rows, "query_results.jsonl")
