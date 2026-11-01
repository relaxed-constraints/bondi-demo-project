# Step 2: prepare your database

## What we will do

We will use BONDI's deployment API to deploy a local MongoDB instance, then download and insert the [electric vehicles
dataset](./1_general.md#dataset) into it.

## Before starting

Make sure you have installed Docker and have gone through the Python environment setup for this project, as described in the [README](../README.md#setup).

## Read these three files

1. [src/bondi_demo/data.py](../src/bondi_demo/data.py): data download and batched import utilities. The actual logic for handling the dataset resides here.
2. [experiments/prepare_db.py](../experiments/prepare_db.py): experiment script to deploy MongoDB, calls the data functions,
   and logs some results.
3. [experiments/configs/prepare.yaml](../experiments/configs/prepare.yaml): the few settings you can change.


### 1. Data helper functions

You'll find 2 main functions in `src/bondi_demo/data.py` for handling the dataset:

- `download_dataset()`: downloads the dataset from Huggingface and caches it locally. We use the [Huggingface Hub](https://huggingface.co/docs/huggingface_hub) library for this purpose.
- `import_dataset()`: reads the cached dataset and inserts it into MongoDB in batches. We could have used a command line tool like `mongoimport` here, but we want to automate everything through scripts, so we can run this entire process programmatically.

The unit tests for this functionality are located in `tests/test_data.py`. Feel free to look through it as it may help you better understand how the dataset handling functions work.


### 2. The experiment script

The experiment script is under `experiments/prepare_db.py` and makes use of the data helper functions among other utilities. It executes the following steps: 

1. **Reading yanex parameters** (further reading: [Parameter Access](https://github.com/rueckstiess/yanex/blob/main/docs/run-api.md#parameter-access) documentation or the Yanex examples [1 Basic Usage](https://github.com/rueckstiess/yanex/blob/main/examples/cli/01_basic_usage/README.md) and [2 Configuration Files](https://github.com/rueckstiess/yanex/blob/main/examples/cli/02_config_files/README.md))
2. **Deploying MongoDB** using BONDI's deployment API (further reading: [BONDI Deployment](https://relaxed-constraints.github.io/bondi/deployment/))
3. **Downloading the dataset** with `download_dataset()`.
4. **Importing the dataset** into MongoDB with `import_dataset()`.
5. **Saving a manifest artifact** to keep track of the dataset import and other relevant experiment metadata (further reading: [yanex.save_artifact()](https://github.com/rueckstiess/yanex/blob/main/docs/run-api.md#yanexsave_artifactobj-filename-savernone)



## Run your first tracked experiment

Change into the `experiments` directory, then run the following command:

```sh
yanex run prepare_db.py -c configs/prepare.yaml --name "1-prepare"
```


Expect the final messages like:

```text
...
> Imported 189010 records into bondi_demo.electric_vehicles
✓ Experiment completed successfully: 15067bff
  Directory: /Users/<you>/.yanex/experiments/15067bff
```

Yanex prints an experiment ID. Save it: later steps will refer to this completed
run by declaring a dependency with the `-D` option. A dependency links experiment 
provenance and artifacts.

## Inspect the import data

You can run this in a Python notebook using the project's environment:

```python
from pymongo import MongoClient

with MongoClient("mongodb://127.0.0.1:27017/") as client:
    collection = client.bondi_demo.electric_vehicles
    print(collection.count_documents({}))
    print(collection.find_one())
```

If you have the `mongosh` shell installed, you can also inspect the collection directly:

```sh
mongosh
use bondi_demo
db.electric_vehicles.countDocuments()
db.electric_vehicles.findOne()
```

In MongoDB, a **database** groups collections. A **collection** holds documents, and a
**document** is a record resembling a Python dictionary.
See [MongoDB documents](https://www.mongodb.com/docs/manual/core/document/).


## Inspect the Yanex experiment

To see a list of recent Yanex experiments, run:

```sh
yanex list
```

To see more details about a specific experiment, copy one of the experiment IDs from the list and run:

```sh
yanex show <experiment-id>
```

To open the experiment folder in your Windows explorer or Mac Finder, run:

```sh
yanex open <experiment-id>
```

In there, you will find an `artifacts` subdirectory containing the logged artifacts of the experiment.

The run's `dataset_manifest.json` contains the dataset repository, filename,
namespace, document count, local connection URI, and deployment name/image
(when managed by BONDI). Numeric metrics
include `imported_records`.

To access the experiment programmatically, use the following Python code, e.g. in a Python notebook:

```python
import yanex.results as yr

experiment = yr.get_experiment("<experiment-id>")
print(experiment.get_metrics())
```

Read [Yanex Results API](https://github.com/rueckstiess/yanex/blob/main/docs/results-api.md) for accessing existing experiments, their metrics and artifacts. 


## Exercises

1. In a Jupyter notebook, use the Yanex Results API to load an experiment by its ID and retrieve the dataset manifest artifact.
2. Use the deployment name from the manifest and the BONDI Deployment API to stop the deployment programmatically.
3. Restart the same deployment with the `bondi` command line interface. 

---

## Next

[Generate a workload](3_workload.md) from this collection and save it as a dependent Yanex experiment.

