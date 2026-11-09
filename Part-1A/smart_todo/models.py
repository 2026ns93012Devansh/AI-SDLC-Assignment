from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum
from typing import Iterable


class ValidationError(ValueError):
    """Raised when a task field or identifier is invalid."""


class Priority(str, Enum):
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"


class Status(str, Enum):
    PENDING = "Pending"
    COMPLETED = "Completed"


_TASK_ID_PATTERN = re.compile(r"T-(\d{4,})\Z")


def format_task_id(number: int) -> str:
    if number < 1:
        raise ValidationError("Task ID number must be positive.")
    return f"T-{number:04d}"


def task_id_number(task_id: str) -> int:
    if not isinstance(task_id, str):
        raise ValidationError("Task ID must be text.")

    match = _TASK_ID_PATTERN.fullmatch(task_id)
    if match is None:
        raise ValidationError(
            f"Invalid task ID {task_id!r}; expected a value like T-0001."
        )

    number = int(match.group(1))
    if format_task_id(number) != task_id:
        raise ValidationError(
            f"Invalid task ID {task_id!r}; expected a value like T-0001."
        )
    return number


def normalize_title(value: str) -> str:
    if not isinstance(value, str):
        raise ValidationError("Title must be text.")

    normalized = value.strip()
    if not normalized:
        raise ValidationError("Title must not be blank.")
    return normalized


def normalize_description(value: str) -> str:
    if not isinstance(value, str):
        raise ValidationError("Description must be text.")
    return value.strip()


def parse_priority(value: str) -> Priority:
    if isinstance(value, str):
        for priority in Priority:
            if value.casefold() == priority.value.casefold():
                return priority
    valid_values = ", ".join(priority.value for priority in Priority)
    raise ValidationError(f"Invalid priority {value!r}; choose {valid_values}.")


def parse_status(value: str) -> Status:
    if isinstance(value, str):
        for status in Status:
            if value.casefold() == status.value.casefold():
                return status
    valid_values = ", ".join(status.value for status in Status)
    raise ValidationError(f"Invalid status {value!r}; choose {valid_values}.")


def normalize_tags(values: Iterable[str]) -> tuple[str, ...]:
    if isinstance(values, (str, bytes)):
        raise ValidationError("Tags must be supplied as a collection of values.")

    tags: list[str] = []
    seen: set[str] = set()

    for value in values:
        if not isinstance(value, str):
            raise ValidationError("Tags must be text.")
        tag = value.strip()
        if not tag:
            raise ValidationError("Tags must not be empty.")

        key = tag.casefold()
        if key not in seen:
            tags.append(tag)
            seen.add(key)

    return tuple(tags)


@dataclass(frozen=True, slots=True)
class Task:
    id: str
    title: str
    description: str
    priority: Priority
    tags: tuple[str, ...]
    status: Status
