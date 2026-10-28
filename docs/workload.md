# Step 2: generate a workload

A workload is a collection of queries we will run against each index set. Using the
same saved queries makes those benchmarks comparable.

## Read these files

1. `src/bondi_demo/workload.py`: samples documents, infers a schema, and generates queries.
2. `experiments/configs/workload.yaml`: pattern counts, predicate counts, sample size and seed.
3. `experiments/workload.py`: loads the preparation dependency and saves the result with Yanex.

## Run the experiment

Complete [database preparation](walkthrough.md) first, then pass its experiment ID:

```sh
uv run yanex run experiments/workload.py \
  -c experiments/configs/workload.yaml \
  -D prepare=<prepare-experiment-id> -n workload-ev
```

`-D prepare=...` names a Yanex dependency. The script reads `dataset_manifest.json`
from that experiment to find the connection URI and collection namespace. The
prepared database must still be running; use `uv run bondi start bondi-demo` if you
stopped it. Dependencies record lineage; they do not rerun preparation.

The reusable function uses MongoDB's `$sample` to fetch 10,000 documents and BONDI's
schema parser to collect their distinct field values. The generator creates **5
patterns with 20 instances each**, giving **100 queries**. A pattern fixes the fields,
operators and query options; its instances vary the filter values. Each query has
between one and three predicates. Other generator options retain BONDI defaults,
including occasional sorts and limits. There are no selectivity constraints, so
some queries may return no documents or many documents.

`seed` controls query generation, but not MongoDB's random sample. Rerunning may
produce different queries. Reuse the saved artifact for repeatable comparisons.
See [BONDI workload generation](https://relaxed-constraints.github.io/bondi/workload-generation/)
and [Yanex](https://github.com/rueckstiess/yanex) for more details.

## Load and inspect the queries

Yanex saves `workload.jsonl` using BONDI's `Workload.save()` method. Load it in a
notebook or another script with the corresponding loader:

```python
import yanex.results as yr
from bondi.workload import Workload

experiment = yr.get_experiment("<workload-experiment-id>")
workload = experiment.load_artifact("workload.jsonl", loader=Workload.load)

print(f"{len(workload)} queries")
for entry in list(workload)[:3]:
    print(entry.pattern_id, entry.query.filter)
```

Each entry holds its pattern ID and a `MongoFindQuery`. You can also inspect
`entry.query.sort`, `.projection`, `.skip` and `.limit`. The experiment also saves `patterns.jsonl` using each pattern's `to_dict()` method;
restore those rows with `MongoQueryPattern.from_dict()`. Their list positions match
the workload pattern IDs. Metrics include `query_count`, `pattern_count` and
`generation_seconds`.

## Try a small change

Override a parameter without editing the YAML:

```sh
uv run yanex run experiments/workload.py \
  -c experiments/configs/workload.yaml \
  -D prepare=<prepare-experiment-id> -p max_predicates=2
```

Run `uv run pytest` and read `tests/test_workload.py`: it generates real BONDI queries
from a tiny sample and checks the saved artifact without requiring MongoDB.

Next we will benchmark the saved workload against the supplied index sets.
