# Step 5: analyse benchmark results

Analyse the benchmark results interactively in a Jupyter notebook, using the Yanex Results API to access the metrics and artifacts. 

## Read this file

- [notebooks/explore_results.ipynb](../notebooks/explore_results.ipynb): the Jupyter notebook for interactive analysis of benchmark results.


Open the notebook in VS Code with its Jupyter extension.
Run `uv sync --locked` first, then select this project's `.venv/bin/python` as the
notebook kernel. pandas, matplotlib and ipykernel are included as regular dependencies.
MongoDB does not need to be running: the notebook reads saved Yanex results.

Run cells from top to bottom. The notebook teaches:

1. Comparing runs and their metrics with `yr.compare()`.
2. Manipulating the resulting DataFrame for further analysis, such as column cleanup, baseline comparisons and speedup calculations.
3. Plotting the main metric as a bar chart.
4. Loading individual query results from the experiment's artifacts and grouping and aggregating the results into summary statistics.
5. Plotting execution times by patterns.
6. Loading BONDI patterns to interpret which indexes helped.


For repeated experiments with different parameters, workloads or index sets, you can use tags to group your runs together. Either use the `--tag` or `-t` option with `yanex run` or add tags afterwards with the `yanex update --add-tag` command.

Then add `tags=["my-comparison"]` to `yr.compare()` and `yr.get_experiments()` calls in the notebook to filter on those specific runs.