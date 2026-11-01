# Step 4: compare index sets

Run the same saved workload with three different index sets. The question is:
**which set makes this workload fastest?**

## Read these files

1. [src/bondi_demo/benchmark.py](../src/bondi_demo/benchmark.py): replace indexes and measure queries using BONDI.
2. [experiments/benchmark.py](../experiments/benchmark.py): load dependencies, call the helpers, and save Yanex results.
3. [experiments/configs/benchmark.yaml](../experiments/configs/benchmark.yaml): the three index sets and measurement settings.


The helpers are ordinary Python functions you can also call from tests or notebooks.

## How index sets are represented

One YAML file contains all index sets, the active set is specified with the `index_set` parameter. An index is an ordered list of `[field, direction]` pairs: `1` means ascending and `-1` means descending.

| `index_set` | Indexes |
| --- | --- |
| `baseline` | No secondary indexes |
| `single` | Separate indexes on City, Model Year, State, Make, Color |
| `compound` | Compound indexes on (Make, Model Year), (City, Color, Model Year), (State, Color), (Make, City) |

The baseline is represented by an empty list.

Field order matters in a compound index. These are deliberately simple candidate
sets, not recommendations tailored to the generated workload. MongoDB chooses
whether to use them; adding an index does not guarantee a faster query.
See [MongoDB indexes](https://www.mongodb.com/docs/manual/indexes/) for the concepts.

## Run the comparison

Use the experiment ID from [workload generation](3_workload.md) for **all three runs**. You can retrieve it by listing the latest experiments with `yanex list`. 

From the `experiments` directory:

```sh
yanex run benchmark.py \
  -c configs/benchmark.yaml \
  -D workload=<workload-id> -p index_set=baseline,single,compound \
  -n "3-benchmark"
```

The `-p index_set=baseline,single,compound` syntax tells yanex to run one experiment for each of the 3 comma-separated values. 

Make sure to include the `-n` (short for `--name`) argument as we will use the experiment name to filter the results later. 

The script loads `workload.jsonl` from its direct dependency (the previously run workload experiment). Yanex finds
`dataset_manifest.json` through the workload's preparation ancestor, so no second
`-D` argument or repeated connection settings are needed. Yanex has access to all artifacts from the dependency graph. 

## What we measure

The defaults are one warm-up pass followed by three measured executions in sequence, with concurrency fixed at one (no parallelism). BONDI consumes each query's full cursor but
does not retain the documents. Index creation and warm-ups are outside the timings.

Each query has a 60-second timeout. Measured errors are saved. If any of the queries fails, the experiment
fails as a whole rather than reporting an incomplete workload as a fast result. 

We log the median execution time `median_workload_ms` across all repetitions, and a list of execution times per workload `workloads_ms` as a Yanex metrics with
`yanex.log_metrics()`. These can then be retrieved in the analysis phase using the Yanex Results API.

**Artifacts**:

- `query_results.jsonl`: repetition, query ID, pattern ID, elapsed milliseconds,
  returned row count, status and error.

The main metric is `median_workload_ms`, the median of those pass totals. These are
client-observed execution times, including result fetching, rather than server-only
explain statistics. Warm-up helps
reduce first-pass effects but does not enforce identical cache conditions. 

## Inspect results

First, run `yanex list` to see the recent experiments. You should find 3 benchmark experiments named `3-benchmark-baseline`, `3-benchmark-single`, and `3-benchmark-compound`. Yanex automatically appends `-<value>` to the experiment base names when it executes a sweep over parameter values.

We will use the experiment name prefix `3-benchmark` to filter the results (note the asterisk `*` in the filter below). 

Run this code in a Jupyter notebook or Python shell. 

```python
from pprint import pprint

import yanex.results as yr

exps = yr.get_experiments(name="3-benchmark*")
metrics = {e.get_param("index_set"): e.get_metrics(as_dataframe=False) for e in exps}

pprint(metrics)
```

## Exercise

Add another entry (e.g. `mine`) to the `indexes` dictionary in the config file, then run a 4th experiment with `-p index_set=mine` and `-n "3-benchmark-mine"`. Don't forget to declare the workload dependency!

Then compare the metrics using the command line with `yanex compare`. Filter on the experiment name prefix with `--name "3-benchmark*"` to see the 4 benchmark experiments. 

Were you able to beat the other 3 index strategies in terms of `median_workload_ms`?

## Next

[Analyse the results](5_analysis.md) in the notebook. It discovers benchmark
experiments through Yanex filters, so you do not need to copy their IDs manually.
