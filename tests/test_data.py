"""Verify demo policy around BONDI's source reader and database writer."""

from unittest.mock import MagicMock, patch

import pytest
from bondi import MongoConnection
from bondi.data import LoadDataResult
from bondi.mongodb import MongoCollectionRef

from bondi_demo import data

URI = "mongodb://localhost:27126"


@pytest.fixture
def loading():
    client = MagicMock()
    database = client.__enter__.return_value[data.DATABASE]
    database.list_collection_names.return_value = []
    database[data.COLLECTION].count_documents.return_value = 3
    receipt = LoadDataResult("mongodb", destinations={f"{data.DATABASE}.{data.COLLECTION}": 3})
    with (
        patch.object(data, "MongoClient", return_value=client) as connect,
        patch.object(data, "download_dataset") as download,
        patch.object(data, "load_hf_dataset", return_value=receipt) as load,
    ):
        yield database, connect, download, load


def test_bondi_receives_exact_pinned_source_and_destination(loading):
    database, connect, download, load = loading
    download.side_effect = lambda: connect.assert_not_called()
    assert data.load_dataset(URI, batch_size=2, expected_records=3) == 3
    load.assert_called_once_with(
        data.DATASET_REPO,
        target=MongoConnection(URI),
        collection=MongoCollectionRef(data.DATABASE, data.COLLECTION),
        dataset="electric_vehicles",
        split="train",
        revision=data.DATASET_REVISION,
        streaming=False,
        json_mode="plain",
        mode="create",
        batch_size=2,
    )
    database.drop_collection.assert_not_called()
    database.create_collection.assert_called_once_with(data.COLLECTION)
    connect.return_value.__exit__.assert_called_once()


def test_existing_collection_requires_explicit_reset(loading):
    database, _, _, load = loading
    database.list_collection_names.return_value = [data.COLLECTION]
    with pytest.raises(ValueError, match="already exists"):
        data.load_dataset(URI)
    database.drop_collection.assert_not_called()
    database.create_collection.assert_not_called()
    load.assert_not_called()
    data.load_dataset(URI, expected_records=3, reset=True)
    database.drop_collection.assert_called_once_with(data.COLLECTION)


@pytest.mark.parametrize("failure", [RuntimeError("write failed"), KeyboardInterrupt()])
def test_load_failure_or_interruption_removes_partial_import(loading, failure):
    database, _, _, load = loading
    load.side_effect = failure
    with pytest.raises(type(failure)):
        data.load_dataset(URI)
    database.drop_collection.assert_called_once_with(data.COLLECTION)


@pytest.mark.parametrize("expected,observed", [(4, 3), (3, 2)])
def test_wrong_count_removes_import(loading, expected, observed):
    database, _, _, _ = loading
    database[data.COLLECTION].count_documents.return_value = observed
    with pytest.raises(ValueError, match="Expected"):
        data.load_dataset(URI, expected_records=expected)
    database.drop_collection.assert_called_once_with(data.COLLECTION)


def test_checksum_failure_precedes_database_changes(loading):
    _, connect, download, load = loading
    download.side_effect = ValueError("checksum mismatch")
    with pytest.raises(ValueError, match="checksum"):
        data.load_dataset(URI, reset=True)
    connect.assert_not_called()
    load.assert_not_called()


@pytest.mark.parametrize(
    "option,value",
    [("batch_size", 0), ("batch_size", True), ("expected_records", 0), ("expected_records", True)],
)
def test_invalid_options_do_not_download_or_connect(loading, option, value):
    _, connect, download, _ = loading
    with pytest.raises(ValueError):
        data.load_dataset(URI, **{option: value})
    download.assert_not_called()
    connect.assert_not_called()


def test_checksum_mismatch(tmp_path):
    path = tmp_path / "records.jsonl"
    path.write_text("{}\n")
    with patch.object(data, "hf_hub_download", return_value=str(path)):
        with pytest.raises(ValueError, match="checksum"):
            data.download_dataset()


def test_download_uses_pinned_revision(tmp_path):
    path = tmp_path / "records.jsonl"
    path.write_text("{}\n")
    with patch.object(data, "hf_hub_download", return_value=str(path)) as download:
        with patch.object(data, "DATASET_SHA256", data.file_sha256(path)):
            assert data.download_dataset() == path
    assert download.call_args.kwargs["revision"] == data.DATASET_REVISION
    assert download.call_args.kwargs["filename"] == data.DATASET_FILE
