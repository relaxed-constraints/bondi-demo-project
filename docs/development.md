# Development

Keep reusable logic in `src/` and add offline tests under `tests/`.
Update docstrings and guides when behavior changes.

With uv, `uv sync --locked` installs the development tools. With pip, install them
in the active environment:

```sh
python -m pip install pytest ruff
```

Run checks from the repository root:

```sh
pytest
ruff check .
ruff format --check .
zensical build --strict
```

These checks do not start databases. Keep future live database tests explicitly
opt-in and separate from the default CI suite.
