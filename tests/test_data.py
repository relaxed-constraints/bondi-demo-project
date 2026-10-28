"""Small files and fake database calls test import behavior without Docker."""

from unittest.mock import MagicMock, patch

import pytest

from bondi_demo import data


@pytest.fixture
def database():
    db = MagicMock()
    db.name = data.DATABASE
    db.list_collection_names.return_value = []
    db.create_collection.return_value.count_documents.return_value = 3
    return db


@pytest.fixture
def records(tmp_path):
    path = tmp_path / "records.jsonl"
    path.write_text('{"Make":"TESLA"}\n\n{"Make":"FORD"}\n{"Make":"BMW"}\n')
    return path


def test_batches_and_final_partial_batch(records, database):
    assert data.import_dataset(records, database, batch_size=2, expected_records=3) == 3
    calls = database.create_collection.return_value.insert_many.call_args_list
    assert [len(call.args[0]) for call in calls] == [2, 1]
    assert calls[0].args[0][0] == {"Make": "TESLA"}
    database.drop_collection.assert_not_called()


def test_existing_collection_requires_explicit_reset(records, database):
    database.list_collection_names.return_value = [data.COLLECTION]
    with pytest.raises(ValueError, match="already exists"):
        data.import_dataset(records, database)
    database.drop_collection.assert_not_called()
    database.create_collection.assert_not_called()
    data.import_dataset(records, database, expected_records=3, reset=True)
    database.drop_collection.assert_called_once_with(data.COLLECTION)


@pytest.mark.parametrize("failure", [RuntimeError("write failed"), KeyboardInterrupt()])
def test_write_failure_or_interruption_removes_partial_import(records, database, failure):
    database.create_collection.return_value.insert_many.side_effect = failure
    with pytest.raises(type(failure)):
        data.import_dataset(records, database, batch_size=1)
    database.drop_collection.assert_called_once_with(data.COLLECTION)


def test_wrong_count_removes_import(records, database):
    with pytest.raises(ValueError, match="Expected"):
        data.import_dataset(records, database, expected_records=4)
    database.drop_collection.assert_called_once_with(data.COLLECTION)


def test_invalid_json_object_removes_import(records, database):
    records.write_text("[]\n")
    with pytest.raises(ValueError, match="JSON object"):
        data.import_dataset(records, database)
    database.drop_collection.assert_called_once_with(data.COLLECTION)


def test_other_database_is_never_modified(records, database):
    database.name = "research"
    with pytest.raises(ValueError, match="restricted"):
        data.import_dataset(records, database, reset=True)
    database.drop_collection.assert_not_called()


def test_checksum_mismatch(records):
    with patch.object(data, "hf_hub_download", return_value=str(records)):
        with pytest.raises(ValueError, match="checksum"):
            data.download_dataset()


def test_download_uses_pinned_revision(records):
    with patch.object(data, "hf_hub_download", return_value=str(records)) as download:
        with patch.object(data, "DATASET_SHA256", data.file_sha256(records)):
            assert data.download_dataset() == records
    assert download.call_args.kwargs["revision"] == data.DATASET_REVISION
    assert download.call_args.kwargs["filename"].endswith("train.jsonl")


def test_docker_waits_for_mongodb_only(tmp_path):
    response = MagicMock()
    response.__enter__.return_value.read.return_value = b"services: {}\n"
    with patch.object(data, "urlopen", return_value=response):
        with patch.object(data.subprocess, "run") as run:
            data.start_database(tmp_path / "compose.yaml")
    command = run.call_args.args[0]
    assert "--wait" in command
    assert command[-1] == "mongodb"
    assert "down" not in command
    assert run.call_args.kwargs["check"] is True
