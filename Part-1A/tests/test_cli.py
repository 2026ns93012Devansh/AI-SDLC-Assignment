import json

import pytest

from smart_todo.cli import main


def test_cli_add_list_update_delete(tmp_path, capsys):
    storage_path = tmp_path / "tasks.json"

    assert (
        main(
            [
                "--file",
                str(storage_path),
                "add",
                "--title",
                "Example",
                "--priority",
                "high",
                "--tag",
                "Work",
                "--description",
                "Details",
            ]
        )
        == 0
    )
    assert "Added task T-0001." in capsys.readouterr().out

    assert main(["--file", str(storage_path), "list", "--sort", "priority"]) == 0
    listed = capsys.readouterr().out
    assert "Example" in listed
    assert "Work" in listed
    assert "Details" in listed

    assert (
        main(
            [
                "--file",
                str(storage_path),
                "update",
                "T-0001",
                "--status",
                "completed",
            ]
        )
        == 0
    )
    capsys.readouterr()

    assert main(["--file", str(storage_path), "delete", "T-0001"]) == 0
    assert "Deleted task T-0001." in capsys.readouterr().out
    assert json.loads(storage_path.read_text(encoding="utf-8"))["tasks"] == []


def test_cli_unknown_id_reports_error_and_nonzero_status(tmp_path, capsys):
    storage_path = tmp_path / "tasks.json"

    result = main(["--file", str(storage_path), "delete", "T-0001"])

    assert result == 2
    assert "not found" in capsys.readouterr().err
    assert not storage_path.exists()


def test_cli_invalid_id_is_rejected_by_argument_parser(tmp_path):
    with pytest.raises(SystemExit) as result:
        main(["--file", str(tmp_path / "tasks.json"), "delete", "not-an-id"])

    assert result.value.code == 2
