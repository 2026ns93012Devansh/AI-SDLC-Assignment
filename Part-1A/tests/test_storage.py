import json

import pytest

from smart_todo.manager import TaskManager
from smart_todo.storage import JsonTaskStore, StorageError


def test_missing_and_empty_files_load_as_empty(tmp_path):
    missing = tmp_path / "missing.json"
    empty = tmp_path / "empty.json"
    empty.write_bytes(b"")

    assert JsonTaskStore(missing).load().next_id == 1
    assert JsonTaskStore(missing).load().tasks == ()
    assert JsonTaskStore(empty).load().next_id == 1
    assert JsonTaskStore(empty).load().tasks == ()


@pytest.mark.parametrize(
    "contents",
    [
        "{",
        " ",
        '{"schema_version": 1, "schema_version": 1, "next_id": 1, "tasks": []}',
        '{"schema_version": 2, "next_id": 1, "tasks": []}',
        '{"schema_version": 1, "next_id": 1, "tasks": [{"id": "T-0001"}]}',
    ],
)
def test_invalid_storage_is_reported_without_replacement(tmp_path, contents):
    storage_path = tmp_path / "tasks.json"
    original = contents.encode("utf-8")
    storage_path.write_bytes(original)

    with pytest.raises(StorageError):
        TaskManager(storage_path)

    assert storage_path.read_bytes() == original


def test_non_utf8_storage_is_reported(tmp_path):
    storage_path = tmp_path / "tasks.json"
    storage_path.write_bytes(b"\xff")

    with pytest.raises(StorageError, match="UTF-8"):
        JsonTaskStore(storage_path).load()


def test_valid_storage_round_trips(tmp_path):
    storage_path = tmp_path / "tasks.json"
    manager = TaskManager(storage_path)
    task = manager.add(title="Persisted", tags=["Work"])

    loaded = JsonTaskStore(storage_path).load()

    assert loaded.next_id == 2
    assert loaded.tasks == (task,)
    document = json.loads(storage_path.read_text(encoding="utf-8"))
    assert document["schema_version"] == 1


def test_failed_write_preserves_existing_file(tmp_path):
    storage_path = tmp_path / "missing" / "tasks.json"
    manager = TaskManager(storage_path)

    with pytest.raises(StorageError, match="Could not write"):
        manager.add(title="Not persisted")

    assert not storage_path.exists()
    assert manager.list_tasks() == []
