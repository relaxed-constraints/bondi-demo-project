# Step 1: prepare your database

## What you will learn

Download a reproducible dataset, import JSON documents into MongoDB, and record the
preparation as a Yanex experiment. The ordinary Python functions are reusable in
notebooks and tests; only the experiment script depends on Yanex.

## Before starting

Install [uv](https://docs.astral.sh/uv/getting-started/installation/) and
[Docker Desktop](https://docs.docker.com/desktop/) (or Docker Engine with Compose v2
on Linux). Start Docker, then run `uv sync --locked` from this repository root.
Select this project's `.venv` as your editor's Python interpreter.

MongoDB binds to localhost port 27017. An existing BONDI MongoDB container is reused.
If another MongoDB installation occupies that port, resolve the conflict first;
do not stop an unfamiliar database. `start_docker=false` lets you explicitly use
an already running local MongoDB instead.

## Read these three files

1. `experiments/configs/prepare.yaml`: the few settings you can change.
2. `src/bondi_demo/data.py`: downloads, Docker startup, and batched import.
3. `experiments/prepare_db.py`: reads settings, calls those functions, and saves results.

`uv sync` installs `bondi_demo` editably: changes under `src/` are immediately
available to scripts, notebooks, and tests. No `sys.path` changes are needed.

## Run your first tracked experiment

```sh
uv run yanex run experiments/prepare_db.py -c experiments/configs/prepare.yaml -n prepare-ev
```

The script fetches BONDI's Compose file from a pinned source revision into ignored
`data/compose.yaml`, starts only its MongoDB service, and waits for readiness.
The first run also downloads the MongoDB image.

It downloads only `electric_vehicles/train.jsonl` from
[origami-ml/jsynth-data](https://huggingface.co/datasets/origami-ml/jsynth-data), pinned
to a particular revision and checked against its SHA-256 checksum. Hugging Face
caches the download, so subsequent runs do not need to download the data again.
No Hugging Face account or token is required.

The file contains 189,010 JSON objects, one per line (JSONL), about 80.8 MB.
Each object becomes a MongoDB document in `bondi_demo.electric_vehicles`.
Inserts use batches of 1,000, rather than holding the whole file in memory.
Original field names and values are preserved; MongoDB adds `_id` identifiers.
Registration dates remain epoch-millisecond numbers, not BSON dates.

Expect a final message like:

```text
Ready: bondi_demo.electric_vehicles (189,010 documents)
```

Yanex prints an experiment ID. Save it: later steps will refer to this completed
run using `-D`. A dependency links experiment provenance and artifacts; it does
not start a stopped database or restore changed collection contents.

## Inspect what you imported

You can run this in a Python notebook using the project's environment:

```python
from pymongo import MongoClient

with MongoClient("mongodb://127.0.0.1:27017/") as client:
    collection = client.bondi_demo.electric_vehicles
    print(collection.count_documents({}))
    print(collection.find_one({}, {"_id": 0, "Make": 1, "Model Year": 1}))
```

A **database** groups collections. A **collection** holds documents, and a
**document** is a record resembling a Python dictionary.
See [MongoDB documents](https://www.mongodb.com/docs/manual/core/document/).

## Inspect the experiment

```sh
uv run yanex list
```

The run's `dataset_manifest.json` contains the dataset repository/revision, filename,
checksum, namespace, document count, and local connection URI. Numeric metrics
include `imported_records` and total `prepare_seconds` (including startup/download).
Yanex stores these under `~/.yanex/experiments/` by default, outside this repository.

```python
import yanex.results as yr

experiment = yr.get_experiment("<your-experiment-id>")
print(experiment.load_artifact("dataset_manifest.json"))
```

Read [Yanex](https://github.com/rueckstiess/yanex) for parameters and artifact access.
The large dataset is cached, not copied into each experiment's artifacts.

## Reruns and cleanup

An existing collection causes preparation to fail rather than duplicate its rows.
To deliberately replace **only the demo collection**, including its indexes:

```sh
uv run yanex run experiments/prepare_db.py -c experiments/configs/prepare.yaml -p reset=true
```

Do not run two preparation experiments at once. A failed/interrupted import removes
its partial collection, but a forced process kill or machine crash may leave one;
use an explicit reset to recover. Reset does not restore the previous collection
if the replacement fails.

MongoDB stays running for the following steps. To stop it without deleting data:

```sh
docker compose -f data/compose.yaml stop mongodb
```

This also stops MongoDB for other projects using the shared BONDI container.

## Exercise: follow the separation of concerns

Run `uv run pytest` and read `tests/test_data.py`. It uses tiny files and a fake
database to test batching, overwrite protection, count checks, and failure cleanup
without Docker or downloads. Change `batch_size` in the YAML and rerun preparation
with an explicit reset. The record count should remain unchanged.

Next we will generate a workload from this collection and save it as a dependent
Yanex experiment. That stage is not implemented yet.
