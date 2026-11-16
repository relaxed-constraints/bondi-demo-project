"""Download the EV dataset and prepare a local MongoDB collection.

These functions have no Yanex dependency: scripts, notebooks and tests can all
call them directly. BONDI owns source decoding and batched database writes.
"""

from bondi import MongoConnection
from bondi.data import load_hf_dataset
from bondi.mongodb import MongoCollectionRef
from pymongo import MongoClient

DATASET_REPO = "origami-ml/jsynth-data"
DATASET_CONFIG = "electric_vehicles"
DATASET_SPLIT = "train"
EXPECTED_RECORDS = 189010
DATABASE = "bondi_demo"
COLLECTION = "electric_vehicles"


def load_dataset(
    uri: str,
    *,
    batch_size: int = 1000,
    expected_records: int = EXPECTED_RECORDS,
    reset: bool = False,
) -> int:
    """Load the EV training split through BONDI and verify its count.

    Refuse an existing collection
    unless reset=True; reset removes the dedicated demo collection and its indexes.
    Remove partial data on failure, including Ctrl-C. Run preparation sequentially.
    """
    if type(batch_size) is not int or batch_size < 1:
        raise ValueError("batch_size must be a positive integer")
    if type(expected_records) is not int or expected_records < 1:
        raise ValueError("expected_records must be a positive integer")

    with MongoClient(uri, serverSelectionTimeoutMS=10000) as client:
        database = client[DATABASE]
        if COLLECTION in database.list_collection_names():
            if not reset:
                raise ValueError("Demo collection already exists; use reset=true to replace it")
            database.drop_collection(COLLECTION)

        try:
            result = load_hf_dataset(
                DATASET_REPO,
                target=MongoConnection(uri),
                collection=MongoCollectionRef(DATABASE, COLLECTION),
                dataset=DATASET_CONFIG,
                split=DATASET_SPLIT,
                streaming=False,
                json_mode="plain",
                mode="create",
                batch_size=batch_size,
            )
            count = result.destinations[f"{DATABASE}.{COLLECTION}"]
            observed = database[COLLECTION].count_documents({})
            if count != expected_records or observed != count:
                raise ValueError(
                    f"Expected {expected_records} records, loaded {count}, found {observed}"
                )
            return count
        except BaseException:
            # BONDI reports partial writes; this demo owns the cleanup policy.
            database.drop_collection(COLLECTION)
            raise
