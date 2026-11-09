import json
import sys
from datetime import datetime
from pathlib import Path

import requests
from jsonschema import Draft202012Validator, FormatChecker
from jsonschema.exceptions import ValidationError

BASE_DIR = Path(__file__).resolve().parent.parent
DATASET_PATH = BASE_DIR / "evals" / "dataset.json"
SCHEMA_PATH = BASE_DIR / "src" / "output_schema.json"
EVIDENCE_DIR = BASE_DIR / "evidence"

sys.path.insert(0, str(BASE_DIR))

from src.reminder_agent import MODEL_NAME, extract_reminder

THRESHOLD = 0.80


def load_json(path):
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def check_invariants(result):
    """Independent structural and behavioural checks."""
    problems = []

    if result["status"] == "ready":
        if result["needs_clarification"]:
            problems.append("Ready result requests clarification")

        for field in ("title", "date", "time"):
            if not result[field]:
                problems.append(f"Ready result has missing {field}")

    if result["status"] == "needs_clarification" and not result["needs_clarification"]:
        problems.append("Clarification status has false flag")

    if result["date"] is not None:
        try:
            datetime.strptime(result["date"], "%Y-%m-%d")
        except ValueError:
            problems.append("Date is not a valid calendar date")

    if result["time"] is not None:
        try:
            datetime.strptime(result["time"], "%H:%M")
        except ValueError:
            problems.append("Time is not valid 24-hour time")

    return problems


def score_result(actual, expected):
    """Compare all six output fields with the dataset oracle."""
    fields = ["title", "date", "time", "priority", "status", "needs_clarification"]

    correct = sum(actual.get(field) == expected.get(field) for field in fields)

    return correct / len(fields)


def main():
    dataset = load_json(DATASET_PATH)
    schema = load_json(SCHEMA_PATH)

    validator = Draft202012Validator(schema, format_checker=FormatChecker())

    results = []
    scores = []

    print(f"Model: {MODEL_NAME}")
    print(f"Evaluation cases: {len(dataset['cases'])}")
    print(f"Pass threshold: {THRESHOLD:.0%}")
    print("-" * 60)

    for case in dataset["cases"]:
        case_id = case["id"]
        print(f"\nRunning {case_id}: {case['input']}")

        record = {
            "id": case_id,
            "input": case["input"],
            "expected": case["expected"],
            "actual": None,
            "schema_valid": False,
            "invariants_passed": False,
            "semantic_score": 0.0,
            "errors": [],
        }

        try:
            actual = extract_reminder(
                case["input"], reference_date=dataset["metadata"]["reference_date"]
            )

            record["actual"] = actual

            schema_errors = list(validator.iter_errors(actual))
            record["schema_valid"] = not schema_errors

            if schema_errors:
                record["errors"].extend(error.message for error in schema_errors)

            invariant_errors = check_invariants(actual)
            record["invariants_passed"] = not invariant_errors
            record["errors"].extend(invariant_errors)

            if record["schema_valid"] and record["invariants_passed"]:
                score = score_result(actual, case["expected"])
            else:
                score = 0.0

            record["semantic_score"] = round(score, 4)
            scores.append(score)

            print(
                f"Schema: {record['schema_valid']} | "
                f"Invariants: {record['invariants_passed']} | "
                f"Score: {score:.0%}"
            )

            if record["errors"]:
                print("Errors:", record["errors"])

        except (
            requests.RequestException,
            ValueError,
            KeyError,
            TypeError,
            ValidationError,
        ) as error:
            record["errors"].append(f"{type(error).__name__}: {error}")
            scores.append(0.0)
            print("FAILED:", record["errors"][-1])

        results.append(record)

    aggregate = sum(scores) / len(scores) if scores else 0.0
    passed_cases = sum(
        result["semantic_score"] == 1.0
        and result["schema_valid"]
        and result["invariants_passed"]
        for result in results
    )

    evaluation_passed = aggregate >= THRESHOLD and passed_cases == len(results)

    report = {
        "timestamp": datetime.now().astimezone().isoformat(),
        "model": MODEL_NAME,
        "dataset_version": dataset["metadata"].get("dataset_version"),
        "reference_date": dataset["metadata"]["reference_date"],
        "timezone": dataset["metadata"]["timezone"],
        "temperature": 0,
        "seed": 42,
        "threshold": THRESHOLD,
        "total_cases": len(results),
        "fully_correct_cases": passed_cases,
        "aggregate_score": round(aggregate, 4),
        "evaluation_status": ("PASS" if evaluation_passed else "FAIL"),
        "results": results,
    }

    EVIDENCE_DIR.mkdir(exist_ok=True)

    report_path = EVIDENCE_DIR / "evaluation_report.json"

    with report_path.open("w", encoding="utf-8") as file:
        json.dump(report, file, indent=4, ensure_ascii=False)

    print("\n" + "=" * 60)
    print(f"Fully correct cases: {passed_cases}/{len(results)}")
    print(f"Aggregate score: {aggregate:.2%}")
    print(f"Required threshold: {THRESHOLD:.0%}")
    print(f"Final evaluation: {report['evaluation_status']}")
    print(f"Report saved: {report_path}")

    return 0 if evaluation_passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
