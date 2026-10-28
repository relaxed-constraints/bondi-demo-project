# Step 3: compare index sets

Run the same saved workload with three different index sets. The question is:
**which set makes this workload fastest?** There is no guaranteed winner.

## Read these files

1. `experiments/configs/benchmark.yaml`: the three index sets and measurement settings.
2. `src/bondi_demo/benchmark.py`: replace indexes and measure queries using BONDI.
3. `experiments/benchmark.py`: load dependencies, call the helpers, and save Yanex results.

The helpers are ordinary Python functions you can also call from tests or notebooks.
There is no separate runner class.

## How index sets are represented

One YAML file contains all index sets; `index_set` selects one. An index is an ordered list of
`[field, direction]` pairs: `1` means ascending and `-1` means descending.

| `index_set` | Indexes |
| --- | --- |
| `baseline` | No secondary indexes |
| `single` | Separate indexes on City, Model Year, State, Color |
| `compound` | Compound indexes on (Make, Model Year), (City, Color), (State, Color), (Make, City) |

For example, the baseline is represented by an empty list:

```yaml
index_set: baseline
indexes:
  baseline: []
  single:
    - [[City, 1]]
  compound:
    - [[Make, 1], [Model Year, 1]]
```

This abbreviated example illustrates the format; the config file contains the full sets.

Field order matters in a compound index. These are deliberately simple candidate
sets, not recommendations tailored to the generated workload. MongoDB chooses
whether to use them; adding an index does not guarantee a faster query.
See [MongoDB indexes](https://www.mongodb.com/docs/manual/indexes/) for the concepts.

## Run the comparison

Use the experiment ID from [workload generation](workload.md) for **all three runs**:

```sh
uv run yanex run experiments/benchmark.py \
  -c experiments/configs/benchmark.yaml \
  -D workload=<workload-id> -p 'index_set=baseline,single,compound'
```

Yanex runs this sweep sequentially by default; do not add parallel execution. Each run **drops the collection's secondary indexes** before
creating its own set, and leaves that set installed afterwards. MongoDB's required
`_id_` index remains. The generated workload excludes `_id`, so the baseline setup
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

Next, [analyse the results](analysis.md) in the notebook. It discovers benchmark
experiments through Yanex filters, so you do not need to copy their IDs manually.

## Bonus: index set C

Add a `C` entry to the `indexes` dictionary and select it with `-p index_set=C`.
Inspect the saved workload's patterns to choose fields and their order. Run against
the same workload ID and compare your result with A and B.
