# Installation

Use Python 3.11 or newer and Git. Install Docker with Compose v2 if you plan to
run database experiments. The offline tests and documentation preview do not need Docker.

## Clone the project

```sh
git clone https://github.com/relaxed-constraints/bondi-demo-project.git
cd bondi-demo-project
```

If you are creating a new project, disconnect the template remote before editing:

```sh
git remote remove origin
```

Add your own repository as `origin` when it is ready. Do not push project changes
back to the starter repository.

## Create an environment and install

=== "uv"

    Install [uv](https://docs.astral.sh/uv/getting-started/installation/) first.

    ```sh
    uv sync --locked
    source .venv/bin/activate
    ```

=== "pip"

    ```sh
    python -m venv .venv
    source .venv/bin/activate
    python -m pip install --upgrade pip
    python -m pip install -e .
    ```

    pip reads dependencies from `pyproject.toml`. It does not use `uv.lock`.

On Windows PowerShell, use `.venv\Scripts\Activate.ps1` to activate the environment.
The examples assume an activated environment and commands run from the repository root.

Both routes install BONDI 0.3.1, Yanex 0.7.0 and the documentation tools.
Continue with the [Quickstart](quickstart.md).
