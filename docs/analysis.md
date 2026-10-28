# Step 4: analyse benchmark results

Open `notebooks/compare_indexes.ipynb` in VS Code with its Jupyter extension.
Run `uv sync --locked` first, then select this project's `.venv/bin/python` as the
notebook kernel. pandas, matplotlib and ipykernel are included as regular dependencies.
MongoDB does not need to be running: the notebook reads saved Yanex results.

Run cells from top to bottom. The notebook teaches:

1. Discovering runs with `yr.get_experiments()` filters, including their status.
2. Selecting completed benchmarks for the same workload and measurement settings.
3. Reading one experiment's logged values with `exp.get_metrics()`.
4. Combining metrics with `yr.get_metrics()` and plotting with `yr.plot_metrics()`.
5. Loading `query_results.jsonl` into pandas for per-query statistics.
6. Plotting median times and repetition box plots for every query, grouped by pattern.
7. Loading BONDI patterns to interpret which indexes helped.

By default, it chooses the newest completed run for each index set on the newest
completed benchmark's workload. The selection is printed; it is not a search for
the fastest run. Narrow the discovery filters by tag, name or date when you have
several comparisons. Keep failed runs visible in the initial table, then investigate
them separately rather than treating their partial timings as successful results.

For future comparisons you can tag all three benchmark runs together:

```sh
uv run yanex run experiments/benchmark.py \
  -c experiments/configs/benchmark.yaml \
  -D workload=<workload-id> -p 'index_set=baseline,single,compound' -t comparison-1
```

Then add `tags=["comparison-1"]` to `yr.get_experiments()` in the notebook. Each plot
uses only the selected experiments. Individual query boxes contain three measured
observations with the default benchmark config; they describe variability but are
not confidence intervals. Different pattern figures may have different vertical scales.
