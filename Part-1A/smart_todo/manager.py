from __future__ import annotations

from dataclasses import replace
from pathlib import Path
from typing import Sequence

from smart_todo.models import (
    Priority,
    Status,
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
from smart_todo.storage import JsonTaskStore


class TaskNotFoundError(Exception):
    """Raised when an operation references an ID that is not stored."""


class TaskManager:
    def __init__(self, storage_path: Path) -> None:
        self._store = JsonTaskStore(storage_path)
        data = self._store.load()
        self._tasks = list(data.tasks)
        self._next_id = data.next_id

    def list_tasks(
        self,
        *,
        status: Status | str | None = None,
        priority: Priority | str | None = None,
        tag: str | None = None,
        sort_by: str | None = None,
    ) -> list[Task]:
        parsed_status = parse_status(status) if isinstance(status, str) else status
        parsed_priority = (
            parse_priority(priority) if isinstance(priority, str) else priority
        )
        normalized_tag = normalize_tags([tag])[0] if tag is not None else None
        if sort_by not in (None, "priority"):
            raise ValidationError("Sort field must be 'priority'.")

        matching = [
            task
            for task in self._tasks
            if (parsed_status is None or task.status == parsed_status)
            and (parsed_priority is None or task.priority == parsed_priority)
            and (
                normalized_tag is None
                or any(tag.casefold() == normalized_tag.casefold() for tag in task.tags)
            )
        ]

        if sort_by == "priority":
            priority_order = {
                Priority.HIGH: 0,
                Priority.MEDIUM: 1,
                Priority.LOW: 2,
            }
            return sorted(
                matching,
                key=lambda task: (
                    priority_order[task.priority],
                    task_id_number(task.id),
                ),
            )
        return sorted(matching, key=lambda task: task_id_number(task.id))

    def add(
        self,
        *,
        title: str,
        description: str = "",
        priority: Priority | str = Priority.MEDIUM,
        tags: Sequence[str] = (),
        status: Status | str = Status.PENDING,
    ) -> Task:
        normalized_title = normalize_title(title)
        normalized_description = normalize_description(description)
        parsed_priority = (
            priority if isinstance(priority, Priority) else parse_priority(priority)
        )
        parsed_status = status if isinstance(status, Status) else parse_status(status)
        normalized_tags = normalize_tags(tags)
        task = Task(
            id=format_task_id(self._next_id),
            title=normalized_title,
            description=normalized_description,
            priority=parsed_priority,
            tags=normalized_tags,
            status=parsed_status,
        )

        updated_tasks = [*self._tasks, task]
        updated_next_id = self._next_id + 1
        self._save_and_update(updated_tasks, updated_next_id)
        return task

    def update(
        self,
        task_id: str,
        *,
        title: str | None = None,
        description: str | None = None,
        priority: Priority | str | None = None,
        status: Status | str | None = None,
        tags: Sequence[str] | None = None,
    ) -> Task:
        task_id_number(task_id)
        if all(value is None for value in (title, description, priority, status, tags)):
            raise ValidationError("Supply at least one field to update.")

        index = self._find_task_index(task_id)
        current = self._tasks[index]
        updated = replace(
            current,
            title=normalize_title(title) if title is not None else current.title,
            description=(
                normalize_description(description)
                if description is not None
                else current.description
            ),
            priority=(
                priority
                if isinstance(priority, Priority)
                else parse_priority(priority)
                if priority is not None
                else current.priority
            ),
            status=(
                status
                if isinstance(status, Status)
                else parse_status(status)
                if status is not None
                else current.status
            ),
            tags=normalize_tags(tags) if tags is not None else current.tags,
        )

        updated_tasks = self._tasks.copy()
        updated_tasks[index] = updated
        self._save_and_update(updated_tasks, self._next_id)
        return updated

    def delete(self, task_id: str) -> None:
        task_id_number(task_id)
        index = self._find_task_index(task_id)
        updated_tasks = self._tasks.copy()
        del updated_tasks[index]
        self._save_and_update(updated_tasks, self._next_id)

    def _find_task_index(self, task_id: str) -> int:
        for index, task in enumerate(self._tasks):
            if task.id == task_id:
                return index
        raise TaskNotFoundError(f"Task ID {task_id} was not found.")

    def _save_and_update(self, tasks: list[Task], next_id: int) -> None:
        self._store.save(tasks, next_id)
        self._tasks = tasks
        self._next_id = next_id
