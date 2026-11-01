# Step 3: generate a workload

A workload is a collection of queries we will run against each index set. Using the
same saved queries makes those benchmarks comparable.

## Read these files

1. [src/bondi_demo/workload.py](../src/bondi_demo/workload.py): samples documents, infers a schema, and generates queries.
2. [experiments/workload.py](../experiments/workload.py): loads the preparation dependency and saves the result with Yanex.
3. [experiments/configs/workload.yaml](../experiments/configs/workload.yaml): pattern counts, predicate counts, sample size and seed.

## Run the experiment

Complete [database preparation](2_preparation.md) first, then pass its experiment ID. You can retrieve it by listing the latest experiments with `yanex list`.

```sh
yanex run workload.py \
  -c configs/workload.yaml \
  -D prepare=<prepare-experiment-id> \
  --name "2-workload"
```

`-D prepare=...` names a Yanex dependency. It assigns the experiment with ID `<prepare-experiment-id>` to the `prepare` slot. 

The script uses a guard that ensures an experiment running `prepare_db.py` is available as the `prepare` dependency in the `prepare` slot before proceeding:

```python
yanex.assert_dependency("prepare_db.py", "prepare")
```

The script reads `dataset_manifest.json`
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

## Exercises

### 1. Changing parameters from the command line
Override a parameter without editing the YAML, using `max_predicates=1` on the command line when you run the experiment.

Then inspect the generated queries directly by opening `workload.jsonl`. A quick shortcut to find the file is to use `yanex open <id>`. 

### 2. Inspect the generated patterns

In a notebook, load the `patterns.jsonl` artifact and parse
the patterns back into `MongoQueryPattern` objects, then print
them. What do their printed representations look like? 


## Next

[Benchmark the saved workload](4_benchmark.md) against the supplied index sets.
