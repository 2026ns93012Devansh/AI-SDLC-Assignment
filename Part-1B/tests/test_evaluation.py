import json
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker

from evals.run_evaluation import check_invariants, score_result

BASE_DIR = Path(__file__).resolve().parent.parent
SCHEMA_PATH = BASE_DIR / "src" / "output_schema.json"


def load_validator():
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    return Draft202012Validator(schema, format_checker=FormatChecker())


def test_valid_ready_reminder_passes_invariants():
    result = {
        "title": "Submit my assignment",
        "date": "2026-11-10",
        "time": "09:00",
        "priority": None,
        "status": "ready",
        "needs_clarification": False,
    }

    assert check_invariants(result) == []


def test_ready_reminder_with_missing_time_fails():
    result = {
        "title": "Buy groceries",
        "date": "2026-11-10",
        "time": None,
        "priority": None,
        "status": "ready",
        "needs_clarification": False,
    }

    assert "Ready result has missing time" in check_invariants(result)


def test_clarification_result_passes_invariants():
    result = {
        "title": "Check my email",
        "date": "2026-11-10",
        "time": None,
        "priority": None,
        "status": "needs_clarification",
        "needs_clarification": True,
    }

    assert check_invariants(result) == []


def test_invalid_calendar_date_fails_invariants():
    result = {
        "title": "Check calendar",
        "date": "2026-02-31",
        "time": "09:00",
        "priority": None,
        "status": "ready",
        "needs_clarification": False,
    }

    assert "Date is not a valid calendar date" in check_invariants(result)


def test_invalid_time_fails_invariants():
    result = {
        "title": "Check calendar",
        "date": "2026-11-10",
        "time": "25:70",
        "priority": None,
        "status": "ready",
        "needs_clarification": False,
    }

    assert "Time is not valid 24-hour time" in check_invariants(result)


def test_exact_match_scores_one():
    expected = {
        "title": "Call the bank",
        "date": "2026-11-11",
        "time": "10:30",
        "priority": None,
        "status": "ready",
        "needs_clarification": False,
    }

    assert score_result(expected, expected) == 1.0


def test_one_field_mismatch_reduces_score():
    expected = {
        "title": "Call the bank",
        "date": "2026-11-11",
        "time": "10:30",
        "priority": None,
        "status": "ready",
        "needs_clarification": False,
    }

    actual = expected.copy()
    actual["date"] = "2026-11-12"

    assert score_result(actual, expected) == 5 / 6


def test_valid_output_passes_json_schema():
    result = {
        "title": "Submit my assignment",
        "date": "2026-11-10",
        "time": "09:00",
        "priority": None,
        "status": "ready",
        "needs_clarification": False,
    }

    assert load_validator().validate(result) is None


def test_missing_time_is_allowed_when_clarification_is_required():
    result = {
        "title": "Buy groceries",
        "date": "2026-11-10",
        "time": None,
        "priority": None,
        "status": "needs_clarification",
        "needs_clarification": True,
    }

    assert load_validator().validate(result) is None


def test_invalid_priority_is_rejected_by_schema():
    result = {
        "title": "Finish my project",
        "date": "2026-11-10",
        "time": "09:00",
        "priority": "Urgent",
        "status": "ready",
        "needs_clarification": False,
    }

    assert list(load_validator().iter_errors(result))


def test_dataset_contains_at_least_fifteen_cases():
    dataset_path = BASE_DIR / "evals" / "dataset.json"
    dataset = json.loads(dataset_path.read_text(encoding="utf-8"))

    assert len(dataset["cases"]) >= 15
