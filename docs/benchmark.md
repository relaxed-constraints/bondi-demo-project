# Step 3: compare index sets

Run the same saved workload with three different index sets. The question is:
**which set makes this workload fastest?** There is no guaranteed winner.

## Read these files

1. `experiments/configs/benchmark-*.yaml`: the three index sets and measurement settings.
2. `src/bondi_demo/benchmark.py`: replace indexes and measure queries using BONDI.
3. `experiments/benchmark.py`: load dependencies, call the helpers, and save Yanex results.

The helpers are ordinary Python functions you can also call from tests or notebooks.
There is no separate runner class.

## How index sets are represented

Each YAML file is a complete configuration. An index is an ordered list of
`[field, direction]` pairs: `1` means ascending and `-1` means descending.

| Configuration | Index set |
| --- | --- |
| `benchmark-none.yaml` | No secondary indexes |
| `benchmark-single.yaml` | A: separate indexes on Make, Model Year, County, City |
| `benchmark-compound.yaml` | B: compound indexes on (Make, Model Year) and (County, City) |

For example, set B contains:

```yaml
index_set: B
indexes:
  - [[Make, 1], [Model Year, 1]]
  - [[County, 1], [City, 1]]
```

Field order matters in a compound index. These are deliberately simple candidate
sets, not recommendations tailored to the generated workload. MongoDB chooses
whether to use them; adding an index does not guarantee a faster query.
See [MongoDB indexes](https://www.mongodb.com/docs/manual/indexes/) for the concepts.

## Run the comparison

Use the experiment ID from [workload generation](workload.md) for **all three runs**:

```sh
uv run yanex run experiments/benchmark.py \
  -c experiments/configs/benchmark-none.yaml -D workload=<workload-id> -n no-index

uv run yanex run experiments/benchmark.py \
  -c experiments/configs/benchmark-single.yaml -D workload=<workload-id> -n single-indexes

uv run yanex run experiments/benchmark.py \
  -c experiments/configs/benchmark-compound.yaml -D workload=<workload-id> -n compound-indexes
```

Run these sequentially. Each run **drops the collection's secondary indexes** before
creating its own set, and leaves that set installed afterwards. MongoDB's required
`_id_` index remains. The generated workload excludes `_id`, so the no-index setup
provides the collection-scan baseline. Use the dedicated demo database.

The script loads `workload.jsonl` from its direct dependency. Yanex finds
`dataset_manifest.json` through the workload's preparation ancestor, so no second
`-D` argument or repeated connection settings are needed. The database must still
be running and contain the prepared data.

## What we measure

The defaults are one warm-up pass followed by three measured passes in saved query
order, with concurrency fixed at one. BONDI consumes each query's full cursor but
does not retain the documents. Index creation and warm-ups are outside the timings.

Each query has a 60-second timeout. Measured errors are saved, then the experiment
fails rather than reporting an incomplete workload as a fast result. A failed
warm-up stops the experiment before measurement.

Artifacts:

- `query_results.jsonl`: repetition, query ID, pattern ID, elapsed milliseconds,
  returned row count, status and error.
- `workload_times.json`: the sum of query times for each measured pass.

The main metric is `median_workload_ms`, the median of those pass totals. These are
client-observed execution times, including result fetching, rather than server-only
explain statistics. They exclude Python overhead between queries. Warm-up helps
reduce first-pass effects but does not enforce identical cache conditions. These
small experiments teach measurement; repeat and vary run order before drawing
strong conclusions.

## Inspect results

```python
import yanex.results as yr

experiment = yr.get_experiment("<benchmark-experiment-id>")
rows = experiment.load_artifact("query_results.jsonl")
print(experiment.load_artifact("workload_times.json"))
print(rows[0])
```

Keep the three benchmark IDs for the analysis notebook we will add next.

## Bonus: index set C

Copy a benchmark YAML file and change `index_set` to `C` and its `indexes` list.
Inspect the saved workload's patterns to choose fields and their order. Run against
the same workload ID and compare your result with A and B.
