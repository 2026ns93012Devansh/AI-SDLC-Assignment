from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Sequence

from smart_todo.manager import TaskManager, TaskNotFoundError
from smart_todo.models import (
    Priority,
    Status,
    Task,
    ValidationError,
    parse_priority,
    parse_status,
    task_id_number,
)
from smart_todo.storage import StorageError


def _priority_argument(value: str) -> str:
    try:
        return parse_priority(value).value
    except ValidationError as exc:
        raise argparse.ArgumentTypeError(str(exc)) from exc


def _status_argument(value: str) -> str:
    try:
        return parse_status(value).value
    except ValidationError as exc:
        raise argparse.ArgumentTypeError(str(exc)) from exc


def _task_id_argument(value: str) -> str:
    try:
        task_id_number(value)
    except ValidationError as exc:
        raise argparse.ArgumentTypeError(str(exc)) from exc
    return value


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="smart-todo",
        description="Manage tasks stored in a local JSON file.",
    )
    parser.add_argument(
        "--file",
        type=Path,
        default=Path("tasks.json"),
        help="JSON storage file (default: tasks.json in the current directory)",
    )
    commands = parser.add_subparsers(dest="command", required=True)

    add_parser = commands.add_parser("add", help="add a task")
    add_parser.add_argument("--title", required=True, help="task title")
    add_parser.add_argument("--description", default="", help="optional description")
    add_parser.add_argument(
        "--priority",
        type=_priority_argument,
        choices=[item.value for item in Priority],
        default=Priority.MEDIUM.value,
        metavar="{Low,Medium,High}",
    )
    add_parser.add_argument(
        "--status",
        type=_status_argument,
        choices=[item.value for item in Status],
        default=Status.PENDING.value,
        metavar="{Pending,Completed}",
    )
    add_parser.add_argument(
        "--tag",
        action="append",
        default=[],
        help="task tag; may be supplied more than once",
    )

    list_parser = commands.add_parser("list", help="list, filter, and sort tasks")
    list_parser.add_argument(
        "--status",
        type=_status_argument,
        choices=[item.value for item in Status],
        metavar="{Pending,Completed}",
    )
    list_parser.add_argument(
        "--priority",
        type=_priority_argument,
        choices=[item.value for item in Priority],
        metavar="{Low,Medium,High}",
    )
    list_parser.add_argument("--tag", help="filter by tag")
    list_parser.add_argument(
        "--sort",
        choices=["priority"],
        help="sort by priority (High, Medium, Low)",
    )

    update_parser = commands.add_parser("update", help="update a task")
    update_parser.add_argument("id", type=_task_id_argument, metavar="ID")
    update_parser.add_argument("--title", help="replacement task title")
    update_parser.add_argument(
        "--description", help="replacement description (empty text clears it)"
    )
    update_parser.add_argument(
        "--priority",
        type=_priority_argument,
        choices=[item.value for item in Priority],
        metavar="{Low,Medium,High}",
    )
    update_parser.add_argument(
        "--status",
        type=_status_argument,
        choices=[item.value for item in Status],
        metavar="{Pending,Completed}",
    )
    tag_options = update_parser.add_mutually_exclusive_group()
    tag_options.add_argument(
        "--tag",
        action="append",
        dest="tags",
        help="replacement tag; may be supplied more than once",
    )
    tag_options.add_argument(
        "--clear-tags",
        action="store_true",
        help="remove all tags",
    )

    delete_parser = commands.add_parser("delete", help="delete a task")
    delete_parser.add_argument("id", type=_task_id_argument, metavar="ID")

    return parser


def _render_tasks(tasks: Sequence[Task]) -> str:
    if not tasks:
        return "No tasks found."

    headers = ("ID", "TITLE", "PRIORITY", "TAGS", "STATUS")
    rows: list[tuple[str, str, str, str, str]] = []
    for task in tasks:
        rows.append(
            (
                task.id,
                json.dumps(task.title, ensure_ascii=False),
                task.priority.value,
                json.dumps(list(task.tags), ensure_ascii=False),
                task.status.value,
            )
        )

    widths = [
        max(len(headers[index]), *(len(row[index]) for row in rows))
        for index in range(len(headers))
    ]
    output = [
        " | ".join(
            headers[index].ljust(widths[index]) for index in range(len(headers))
        ),
        "-+-".join("-" * width for width in widths),
    ]
    for task, row in zip(tasks, rows, strict=True):
        output.append(
            " | ".join(row[index].ljust(widths[index]) for index in range(len(headers)))
        )
        if task.description:
            output.append(
                f"  Description: {json.dumps(task.description, ensure_ascii=False)}"
            )
    return "\n".join(output)


def _execute(args: argparse.Namespace) -> int:
    manager = TaskManager(args.file)

    if args.command == "add":
        task = manager.add(
            title=args.title,
            description=args.description,
            priority=args.priority,
            status=args.status,
            tags=args.tag,
        )
        print(f"Added task {task.id}.")
        return 0

    if args.command == "list":
        tasks = manager.list_tasks(
            status=args.status,
            priority=args.priority,
            tag=args.tag,
            sort_by=args.sort,
        )
        print(_render_tasks(tasks))
        return 0

    if args.command == "update":
        tags = [] if args.clear_tags else args.tags
        task = manager.update(
            args.id,
            title=args.title,
            description=args.description,
            priority=args.priority,
            status=args.status,
            tags=tags,
        )
        print(f"Updated task {task.id}.")
        return 0

    if args.command == "delete":
        manager.delete(args.id)
        print(f"Deleted task {args.id}.")
        return 0

    raise AssertionError(f"Unexpected command: {args.command}")


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return _execute(args)
    except (ValidationError, TaskNotFoundError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2
    except StorageError as exc:
        print(f"Storage error: {exc}", file=sys.stderr)
        return 1
