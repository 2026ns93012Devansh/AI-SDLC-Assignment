import json

import pytest

from smart_todo.manager import TaskManager, TaskNotFoundError
from smart_todo.models import Priority, Status, ValidationError


def test_add_uses_defaults_and_persists_next_id(tmp_path):
    storage_path = tmp_path / "tasks.json"
    manager = TaskManager(storage_path)

    first = manager.add(title="  First task  ")
    second = manager.add(
        title="Second task",
        priority="HIGH",
        status="completed",
        tags=[" Work ", "work", "Urgent"],
    )

    assert first.id == "T-0001"
    assert first.title == "First task"
    assert first.priority is Priority.MEDIUM
    assert first.status is Status.PENDING
    assert second.id == "T-0002"
    assert second.priority is Priority.HIGH
    assert second.status is Status.COMPLETED
    assert second.tags == ("Work", "Urgent")

    stored = json.loads(storage_path.read_text(encoding="utf-8"))
    assert stored["next_id"] == 3
    assert [task["id"] for task in stored["tasks"]] == ["T-0001", "T-0002"]


def test_list_filters_combine_with_and_and_tag_matching_is_case_insensitive(
    tmp_path,
):
    manager = TaskManager(tmp_path / "tasks.json")
    manager.add(title="One", status="Pending", priority="High", tags=["Work"])
    manager.add(title="Two", status="Completed", priority="High", tags=["Work"])
    manager.add(title="Three", status="Pending", priority="Low", tags=["Home"])

    tasks = manager.list_tasks(status="pending", priority="high", tag="work")

    assert [task.title for task in tasks] == ["One"]


def test_sort_by_priority_uses_id_as_tie_breaker(tmp_path):
    manager = TaskManager(tmp_path / "tasks.json")
    manager.add(title="Low first", priority="Low")
    manager.add(title="High first", priority="High")
    manager.add(title="High second", priority="High")
    manager.add(title="Medium", priority="Medium")

    tasks = manager.list_tasks(sort_by="priority")

    assert [task.title for task in tasks] == [
        "High first",
        "High second",
        "Medium",
        "Low first",
    ]


def test_update_changes_only_supplied_fields_and_replaces_tags(tmp_path):
    manager = TaskManager(tmp_path / "tasks.json")
    task = manager.add(
        title="Original",
        description="Description",
        priority="Low",
        status="Pending",
        tags=["One", "Two"],
    )

    updated = manager.update(
        task.id,
        title="  Revised  ",
        description="",
        status="Completed",
        tags=[" New ", "new", "Tag"],
    )

    assert updated.title == "Revised"
    assert updated.description == ""
    assert updated.priority is Priority.LOW
    assert updated.status is Status.COMPLETED
    assert updated.tags == ("New", "Tag")


def test_update_can_clear_tags_and_rejects_empty_update(tmp_path):
    manager = TaskManager(tmp_path / "tasks.json")
    task = manager.add(title="Task", tags=["Work"])

    assert manager.update(task.id, tags=[]).tags == ()
    with pytest.raises(ValidationError, match="at least one field"):
        manager.update(task.id)


def test_delete_does_not_reuse_task_ids(tmp_path):
    storage_path = tmp_path / "tasks.json"
    manager = TaskManager(storage_path)
    first = manager.add(title="First")
    manager.delete(first.id)
    second = manager.add(title="Second")

    assert second.id == "T-0002"
    assert [task.id for task in TaskManager(storage_path).list_tasks()] == ["T-0002"]


def test_unknown_ids_do_not_modify_storage(tmp_path):
    storage_path = tmp_path / "tasks.json"
    manager = TaskManager(storage_path)
    task = manager.add(title="Keep")
    before = storage_path.read_bytes()

    with pytest.raises(TaskNotFoundError):
        manager.delete("T-0002")

    assert storage_path.read_bytes() == before
    assert manager.list_tasks() == [task]


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("title", "   "),
        ("priority", "Urgent"),
        ("status", "Paused"),
        ("tags", [""]),
    ],
)
def test_add_rejects_invalid_values(tmp_path, field, value):
    manager = TaskManager(tmp_path / "tasks.json")
    values = {"title": "Valid", field: value}
    with pytest.raises(ValidationError):
        manager.add(**values)
    assert manager.list_tasks() == []
