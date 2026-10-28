# BONDI demo project

A small starting point for learning how to run reproducible MongoDB experiments
with [BONDI](https://relaxed-constraints.github.io/bondi/) and
[Yanex](https://github.com/rueckstiess/yanex).

The research exercise will compare query performance with no secondary indexes,
single-field indexes (set A), and compound indexes (set B). As a bonus exercise,
students will design their own set C.

## 1. Set up Python

Install [uv](https://docs.astral.sh/uv/getting-started/installation/), then run
these commands from this directory:

```sh
uv sync --locked
```

uv installs the selected Python version if needed and creates a `.venv` containing
BONDI, Yanex, pytest, and Ruff. `uv.lock` records the exact dependency versions.
During development, BONDI is installed from the editable sibling checkout
`../bondi`; this provides the deployment API, which is not released on PyPI yet.
Keep that checkout alongside this repository when running `uv sync`.

Use `uv run` to run commands in this environment; activation is not necessary.
In VS Code, select `.venv/bin/python` as your Python interpreter
(`.venv\Scripts\python.exe` on Windows).

## 2. Check your setup

```sh
uv run pytest
uv run ruff check .
uv run ruff format --check .
uv run yanex --help
```

- **pytest** runs automated tests. Read `tests/test_setup.py` for the first example:
  it saves and reloads a BONDI query without connecting to a database.
- **Ruff** checks for common coding mistakes and formats Python consistently.
  Run `uv run ruff format .` to apply formatting.
- **Yanex** will record experiment parameters, results, and dependencies.

Tool documentation: [pytest](https://docs.pytest.org/en/stable/getting-started.html),
[Ruff](https://docs.astral.sh/ruff/), and
[Yanex](https://github.com/rueckstiess/yanex).

## Learning path

Database preparation, workload generation, benchmarking and analysis are implemented. Start with the
[preparation walkthrough](docs/walkthrough.md), then [generate a workload](docs/workload.md)
[benchmark index sets](docs/benchmark.md), and [analyse the results](docs/analysis.md).
We will add the remaining stages incrementally:

1. **Prepare the database:** start MongoDB using BONDI's deployment API, download the
   dataset, import it, and record its provenance with Yanex (`prepare_db.py`).
2. **Generate a workload:** inspect the schema and save a random BONDI workload
   using the preparation experiment as a Yanex dependency (`workload.py`).
3. **Benchmark index sets:** run the same workload with each supplied index set,
   using its experiment as a dependency (`benchmark.py`).
4. **Analyse results:** explore Yanex metrics and per-query measurements in
   `notebooks/compare_indexes.ipynb` ([walkthrough](docs/analysis.md)).
5. **Try your own idea:** add index set C and compare it with the supplied sets.

Each step will introduce only the files and concepts needed for that task.
No database, dataset download, or credentials are required for the current setup tests.

## Dataset

We will use only `electric_vehicles/train.jsonl` from
[origami-ml/jsynth-data](https://huggingface.co/datasets/origami-ml/jsynth-data):
**189,010 records**, approximately **80.8 MB**. The test split is not used.

The download is pinned to revision
`9af20c2698454dd33403c993501f5e1c0007643a` for reproducibility.
Downloaded data and generated results stay out of Git.

## Reusable code and experiments

`src/bondi_demo/data.py` contains ordinary Python functions.
`experiments/prepare_db.py` orchestrates them through Yanex.
The editable package installation lets tests and notebooks import the same functions.

```sh
uv run yanex run experiments/prepare_db.py -c experiments/configs/prepare.yaml -n prepare-ev
```

Install and start Docker first; see the walkthrough for reruns and cleanup.
