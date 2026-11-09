from __future__ import annotations

import json
import os
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

from smart_todo.models import (
    Task,
    ValidationError,
    format_task_id,
    normalize_description,
    normalize_tags,
    normalize_title,
    parse_priority,
    parse_status,
    task_id_number,
)


class StorageError(Exception):
    """Raised when task storage cannot be read, validated, or written."""


@dataclass(frozen=True, slots=True)
class StoreData:
    tasks: tuple[Task, ...]
    next_id: int


def _reject_duplicate_keys(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key {key!r}")
        result[key] = value
    return result


def _require_exact_keys(
    value: object, expected: set[str], context: str
) -> dict[str, object]:
    if not isinstance(value, dict) or set(value) != expected:
        raise StorageError(f"Invalid storage schema in {context}.")
    return value


def _load_task(value: object, index: int) -> Task:
    keys = {"id", "title", "description", "priority", "tags", "status"}
    record = _require_exact_keys(value, keys, f"task {index}")

    task_id = record["id"]
    title = record["title"]
    description = record["description"]
    priority_value = record["priority"]
    tags_value = record["tags"]
    status_value = record["status"]

    if not isinstance(task_id, str):
        raise StorageError(f"Invalid ID in task {index}.")
    try:
        task_number = task_id_number(task_id)
        if format_task_id(task_number) != task_id:
            raise ValidationError("Task ID is not in canonical form.")

        if not isinstance(title, str) or normalize_title(title) != title:
            raise ValidationError("Task title is invalid.")
        if (
            not isinstance(description, str)
            or normalize_description(description) != description
        ):
            raise ValidationError("Task description is invalid.")
        if not isinstance(priority_value, str):
            raise ValidationError("Task priority is invalid.")
        priority = parse_priority(priority_value)
        if priority.value != priority_value:
            raise ValidationError("Task priority is not in canonical form.")
        if not isinstance(status_value, str):
            raise ValidationError("Task status is invalid.")
        status = parse_status(status_value)
        if status.value != status_value:
            raise ValidationError("Task status is not in canonical form.")
        if not isinstance(tags_value, list):
            raise ValidationError("Task tags must be a list.")
        tags = normalize_tags(tags_value)
        if list(tags) != tags_value:
            raise ValidationError("Task tags must be trimmed and unique.")
    except ValidationError as exc:
        raise StorageError(f"Invalid task {index}: {exc}") from exc

    return Task(
        id=task_id,
        title=title,
        description=description,
        priority=priority,
        tags=tags,
        status=status,
    )


class JsonTaskStore:
    def __init__(self, path: Path) -> None:
        self.path = path

    def load(self) -> StoreData:
        try:
            contents = self.path.read_bytes()
        except FileNotFoundError:
            return StoreData(tasks=(), next_id=1)
        except OSError as exc:
            raise StorageError(
                f"Could not read storage file {self.path}: {exc}"
            ) from exc

        if contents == b"":
            return StoreData(tasks=(), next_id=1)

        try:
            text = contents.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise StorageError(f"Storage file {self.path} is not valid UTF-8.") from exc

        try:
            document = json.loads(text, object_pairs_hook=_reject_duplicate_keys)
        except (json.JSONDecodeError, ValueError) as exc:
            raise StorageError(
                f"Storage file {self.path} is not valid JSON: {exc}"
            ) from exc

        try:
            return self._validate_document(document)
        except StorageError as exc:
            raise StorageError(f"Invalid storage file {self.path}: {exc}") from exc

    def _validate_document(self, document: object) -> StoreData:
        record = _require_exact_keys(
            document, {"schema_version", "next_id", "tasks"}, "document"
        )

        version = record["schema_version"]
        next_id = record["next_id"]
        tasks_value = record["tasks"]
        if type(version) is not int or version != 1:
            raise StorageError(f"Unsupported schema version: {version!r}.")
        if type(next_id) is not int or next_id < 1:
            raise StorageError("next_id must be a positive integer.")
        if not isinstance(tasks_value, list):
            raise StorageError("tasks must be a list.")

        tasks = tuple(
            _load_task(value, index) for index, value in enumerate(tasks_value, 1)
        )
        task_numbers = [task_id_number(task.id) for task in tasks]
        if len(set(task_numbers)) != len(task_numbers):
            raise StorageError("Task IDs must be unique.")
        if task_numbers and next_id <= max(task_numbers):
            raise StorageError("next_id must be greater than every stored task ID.")

        return StoreData(tasks=tasks, next_id=next_id)

    def save(self, tasks: Sequence[Task], next_id: int) -> None:
        ordered_tasks = sorted(tasks, key=lambda task: task_id_number(task.id))
        document = {
            "schema_version": 1,
            "next_id": next_id,
            "tasks": [
                {
                    "id": task.id,
                    "title": task.title,
                    "description": task.description,
                    "priority": task.priority.value,
                    "tags": list(task.tags),
                    "status": task.status.value,
                }
                for task in ordered_tasks
            ],
        }

        temporary_path: Path | None = None
        try:
            with tempfile.NamedTemporaryFile(
                mode="w",
                encoding="utf-8",
                dir=self.path.parent,
                prefix=f".{self.path.name}.",
                suffix=".tmp",
                delete=False,
                newline="\n",
            ) as temporary_file:
                temporary_path = Path(temporary_file.name)
                json.dump(document, temporary_file, ensure_ascii=False, indent=2)
                temporary_file.write("\n")

            os.replace(temporary_path, self.path)
            temporary_path = None
        except (OSError, UnicodeError) as exc:
            raise StorageError(
                f"Could not write storage file {self.path}: {exc}"
            ) from exc
        finally:
            if temporary_path is not None:
                try:
                    temporary_path.unlink(missing_ok=True)
                except OSError as exc:
                    raise StorageError(
                        "Could not remove temporary storage file "
                        f"{temporary_path}: {exc}"
                    ) from exc
