"""Download the EV dataset and prepare a local MongoDB collection.

These functions have no Yanex dependency: scripts, notebooks and tests can all
call them directly. Importing data is intentionally separate from downloading it.
"""

import hashlib
import json
from pathlib import Path

from huggingface_hub import hf_hub_download

DATASET_REPO = "origami-ml/jsynth-data"
DATASET_REVISION = "9af20c2698454dd33403c993501f5e1c0007643a"
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


def import_dataset(
    path: Path,
    database,
    *,
    batch_size: int = 1000,
    expected_records: int = EXPECTED_RECORDS,
    reset: bool = False,
) -> int:
    """Stream JSON objects into the dedicated demo collection and verify its count.

    Refuses an existing collection unless reset=True. On failure, removes the
    partial import. Reset permanently replaces the demo collection and its indexes.
    Do not run preparation concurrently against the same database.
    """
    if database.name != DATABASE:
        raise ValueError(f"Import is restricted to the {DATABASE!r} database")
    if type(batch_size) is not int or batch_size < 1:
        raise ValueError("batch_size must be a positive integer")
    if type(expected_records) is not int or expected_records < 1:
        raise ValueError("expected_records must be a positive integer")
    # Check the local file before any destructive action.
    with path.open(encoding="utf-8") as stream:
        if COLLECTION in database.list_collection_names():
            if not reset:
                raise ValueError("Demo collection already exists; use reset=true to replace it")
            database.drop_collection(COLLECTION)
        collection = database.create_collection(COLLECTION)
        try:
            batch = []
            count = 0
            for line_number, line in enumerate(stream, 1):
                if not line.strip():
                    continue
                record = json.loads(line)
                if not isinstance(record, dict):
                    raise ValueError(f"Line {line_number} must be a JSON object")
                batch.append(record)
                count += 1
                if len(batch) >= batch_size:
                    collection.insert_many(batch)
                    batch = []
            if batch:
                collection.insert_many(batch)
            if count != expected_records or collection.count_documents({}) != count:
                raise ValueError(f"Expected {expected_records} records, read {count}")
            return count
        except BaseException:
            # Includes Ctrl-C: leave no partial dataset that looks ready to use.
            database.drop_collection(COLLECTION)
            raise
