"""Download the EV dataset and prepare a local MongoDB collection.

These functions have no Yanex dependency: scripts, notebooks and tests can all
call them directly. BONDI owns source decoding and batched database writes.
"""

import hashlib
from pathlib import Path

from bondi import MongoConnection
from bondi.data import load_hf_dataset
from bondi.mongodb import MongoCollectionRef
from huggingface_hub import hf_hub_download
from pymongo import MongoClient

DATASET_REPO = "origami-ml/jsynth-data"
DATASET_REVISION = "9af20c2698454dd33403c993501f5e1c0007643a"
DATASET_CONFIG = "electric_vehicles"
DATASET_SPLIT = "train"
DATASET_FILE = "electric_vehicles/train.jsonl"
DATASET_SHA256 = "1e3d4375f4a8a9a37abbf083ff4a9fe83b1974ad283d74051cc4e589dc610ea5"
EXPECTED_RECORDS = 189010
DATABASE = "bondi_demo"
COLLECTION = "electric_vehicles"


def file_sha256(path: Path) -> str:
    """Hash file contents without loading the whole file into memory."""
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def download_dataset() -> Path:
    """Download the pinned training file (or reuse the Hugging Face cache)."""
    path = Path(
        hf_hub_download(
            repo_id=DATASET_REPO,
            repo_type="dataset",
            revision=DATASET_REVISION,
            filename=DATASET_FILE,
        )
    )
    if file_sha256(path) != DATASET_SHA256:
        raise ValueError("Dataset checksum does not match the pinned training file")
    return path


def load_dataset(
    uri: str,
    *,
    batch_size: int = 1000,
    expected_records: int = EXPECTED_RECORDS,
    reset: bool = False,
) -> int:
    """Load the pinned EV training split through BONDI and verify its count.

    The checksum is checked before touching MongoDB. Refuse an existing collection
    unless reset=True; reset removes the dedicated demo collection and its indexes.
    Remove partial data on failure, including Ctrl-C. Run preparation sequentially.
    """
    if type(batch_size) is not int or batch_size < 1:
        raise ValueError("batch_size must be a positive integer")
    if type(expected_records) is not int or expected_records < 1:
        raise ValueError("expected_records must be a positive integer")
    download_dataset()

    with MongoClient(uri, serverSelectionTimeoutMS=10000) as client:
        database = client[DATABASE]
        if COLLECTION in database.list_collection_names():
            if not reset:
                raise ValueError("Demo collection already exists; use reset=true to replace it")
            database.drop_collection(COLLECTION)
        database.create_collection(COLLECTION)
        try:
            result = load_hf_dataset(
                DATASET_REPO,
                target=MongoConnection(uri),
                collection=MongoCollectionRef(DATABASE, COLLECTION),
                dataset=DATASET_CONFIG,
                split=DATASET_SPLIT,
                revision=DATASET_REVISION,
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
