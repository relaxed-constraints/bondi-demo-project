# BONDI demo project

A small starting point for learning how to run reproducible MongoDB experiments
with [BONDI](https://relaxed-constraints.github.io/bondi/) and
[Yanex](https://github.com/rueckstiess/yanex). Additionally, we will use `uv` 
as the Python project management tool and Docker to deploy a MongoDB instance locally.

<details>
  <summary><b>What is all this stuff?</b></summary>
  
#### uv

If you're unfamiliar with `uv`, it's worth spending some time to understand its
role in managing virtual environments, dependencies, publishing packages and
running scripts. `uv` is a modern tool for Python project management that
simplifies these tasks compared to traditional approaches using `virtualenv`, 
`pip`, and custom shell scripts.

Read about `uv` features in the [official documentation](https://docs.astral.sh/uv/getting-started/features/). 

#### Docker

Docker is a platform for developing, shipping, and running applications in containers.
Containers package an application and its dependencies, ensuring consistent behavior
across different environments. It makes it very easy to start and manage containerized
services, like databases locally for development and experimentation. 

Read more in the [official Docker documentation](https://docs.docker.com/get-started/).

#### Yanex

Yanex is a generic tool for managing experiments and tracking and analysing their results. 
It allows you to run scripts with specific configurations, record the outputs, and maintain
a history of experiments. This is particularly useful for reproducibility and for 
understanding the impact of different parameters on your results. 

Yanex' documentation can be found on the [Yanex github page](https://github.com/rueckstiess/yanex).

#### BONDI

BONDI is a tooklkit for conducting research with document databases, with a focus on MongoDB. 
It provides tools for deploying databases, generating, running and profiling query workloads, 
analysing the schema of database collections, and estimating cardinalities of queries. 

This repo is an example project demonstrating how to use BONDI for research with MongoDB, 
including dataset preparation, database deployment, and experiment tracking.

More info and the full documentation can be found on the [BONDI documentation site](https://relaxed-constraints.github.io/bondi/).
  
</details>
<br/>

We will first deploy a local MongoDB instance, then download and insert a dataset of electric vehicle
registrations. Then we generate a random query workload based on this dataset. Next, we will evaluate
executing this workload under 3 different index sets: 

- **baseline**: no secondary indexes
- **single**: only single-field indexes
- **compound**: only compound (multi-field) indexes

We want to benchmark how different indexing strategies affect the performance of query execution. 
Finally, we look at the results in a Jupyter notebook to compare the performance of different indexing strategies.

## Setup

### 1. Install Docker

Follow the instructions for your platform on the [Docker website](https://docs.docker.com/get-docker/). After installation, start the Docker daemon to ensure it is running before proceeding with the experiments.

### 2. Set up Python virtual environment and install dependencies

Install [uv](https://docs.astral.sh/uv/getting-started/installation/), then run
this command from the project directory:

```sh
uv sync --locked
```

uv installs the selected Python version if needed and creates a `.venv` containing
all the dependencies. `uv.lock` records the exact dependency versions.

### 3. Check your setup
 
First, from the project directory, activate your virtual environment that `uv` created:

```sh
source .venv/bin/activate
```

Then, check that everything is set up correctly by running the following commands:

```sh
pytest
ruff check .
ruff format --check .
yanex --help
```

- **pytest** runs automated tests. Read `tests/test_setup.py` for the first example:
  it saves and reloads a BONDI query without connecting to a database.
- **Ruff** checks for common coding mistakes and formats Python consistently.
  Run `uv run ruff format .` to apply formatting.
- **Yanex** will record experiment parameters, results, and dependencies.


Tool documentation: [pytest](https://docs.pytest.org/en/stable/getting-started.html),
[Ruff](https://docs.astral.sh/ruff/), and
[Yanex](https://github.com/rueckstiess/yanex).


## Learning Path

There's a guided learning path for understanding this project, available under the `docs/` directory. Each step has a corresponding markdown file explaining the task and how to complete it. We recommend you go through them one by one. 

1. **General information** ([1_general.md](docs/1_general.md)) Some background and overview of the project,
   dataset and the code structure in this repository.
2. **Prepare the database** ([2_preparation.md](docs/2_preparation.md)): start a MongoDB instance locally using BONDI's 
   deployment API, download the dataset, import it, and record its provenance in a Yanex experiment.
3. **Generate a workload** ([3_workload.md](docs/3_workload.md)): inspect the schema and create and save a random query workload using the preparation experiment as a Yanex dependency.
4. **Benchmark index sets** ([4_benchmark.md](docs/4_benchmark.md)): run the same workload with each supplied index set,
   using the previous workload experiment as a dependency.
5. **Analyse results** ([5_analysis.md](docs/5_analysis.md)): explore Yanex metrics and per-query measurements in
   [notebooks/explore_results.ipynb](notebooks/explore_results.ipynb).

Each step will introduce only the files and concepts needed for that task.

