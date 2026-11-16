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
        patch.object(data, "load_hf_dataset", return_value=receipt) as load,
    ):
        yield database, connect, load


def test_bondi_receives_source_and_destination(loading):
    database, connect, load = loading
    assert data.load_dataset(URI, batch_size=2, expected_records=3) == 3
    load.assert_called_once_with(
        data.DATASET_REPO,
        target=MongoConnection(URI),
        collection=MongoCollectionRef(data.DATABASE, data.COLLECTION),
        dataset="electric_vehicles",
        split="train",
        streaming=False,
        json_mode="plain",
        mode="create",
        batch_size=2,
    )
    database.drop_collection.assert_not_called()
    database.create_collection.assert_not_called()
    connect.return_value.__exit__.assert_called_once()


def test_existing_collection_requires_explicit_reset(loading):
    database, _, load = loading
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
    database, _, load = loading
    load.side_effect = failure
    with pytest.raises(type(failure)):
        data.load_dataset(URI)
    database.drop_collection.assert_called_once_with(data.COLLECTION)


@pytest.mark.parametrize("expected,observed", [(4, 3), (3, 2)])
def test_wrong_count_removes_import(loading, expected, observed):
    database, _, _ = loading
    database[data.COLLECTION].count_documents.return_value = observed
    with pytest.raises(ValueError, match="Expected"):
        data.load_dataset(URI, expected_records=expected)
    database.drop_collection.assert_called_once_with(data.COLLECTION)


@pytest.mark.parametrize(
    "option,value",
    [("batch_size", 0), ("batch_size", True), ("expected_records", 0), ("expected_records", True)],
)
def test_invalid_options_do_not_load_or_connect(loading, option, value):
    _, connect, load = loading
    with pytest.raises(ValueError):
        data.load_dataset(URI, **{option: value})
    load.assert_not_called()
    connect.assert_not_called()
