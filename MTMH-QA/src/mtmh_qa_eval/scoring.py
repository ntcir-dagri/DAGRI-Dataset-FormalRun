from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


JsonValue = Any


@dataclass(frozen=True)
class EvaluationResult:
    # Keep the result structure simple so it can be serialized or reused by external systems.
    accuracy: float
    correct: int
    total: int
    missing_ids: list[int]
    unexpected_ids: list[int]
    mismatched_ids: list[int]

    def to_dict(self) -> dict[str, Any]:
        return {
            "accuracy": self.accuracy,
            "correct": self.correct,
            "total": self.total,
            "missing_ids": self.missing_ids,
            "unexpected_ids": self.unexpected_ids,
            "mismatched_ids": self.mismatched_ids,
        }


def load_jsonl(path: str | Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    with Path(path).open("r", encoding="utf-8") as file:
        for line_number, line in enumerate(file, start=1):
            stripped = line.strip()
            if not stripped:
                # Ignore blank lines to be tolerant of lightly edited JSONL files.
                continue
            try:
                record = json.loads(stripped)
            except json.JSONDecodeError as exc:
                raise ValueError(f"Invalid JSON at {path}:{line_number}") from exc
            if not isinstance(record, dict):
                raise ValueError(f"Each JSONL row must be an object: {path}:{line_number}")
            records.append(record)
    return records


def _index_by_id(records: list[dict[str, Any]], path: str | Path) -> dict[int, dict[str, Any]]:
    # Build a unique lookup table by id so we can compare files deterministically.
    indexed: dict[int, dict[str, Any]] = {}
    for row_number, record in enumerate(records, start=1):
        if "id" not in record:
            raise ValueError(f'Missing "id" field in {path}:{row_number}')
        record_id = record["id"]
        if not isinstance(record_id, int):
            raise ValueError(f'"id" must be an integer in {path}:{row_number}')
        if record_id in indexed:
            raise ValueError(f'Duplicate "id" value {record_id} in {path}:{row_number}')
        indexed[record_id] = record
    return indexed


def score_answers(gold_answer: JsonValue, prediction_answer: JsonValue) -> bool:
    # Lists are evaluated as unordered collections for this shared task.
    if isinstance(gold_answer, list) and isinstance(prediction_answer, list):
        return _unordered_list_equals(gold_answer, prediction_answer)

    # Dicts are compared recursively, but their keys must match exactly.
    if isinstance(gold_answer, dict) and isinstance(prediction_answer, dict):
        if set(gold_answer.keys()) != set(prediction_answer.keys()):
            return False
        return all(
            score_answers(gold_answer[key], prediction_answer[key]) for key in gold_answer
        )

    return gold_answer == prediction_answer


def _unordered_list_equals(gold_list: list[JsonValue], prediction_list: list[JsonValue]) -> bool:
    if len(gold_list) != len(prediction_list):
        return False

    # Match each gold item to one still-unused prediction item.
    used_prediction_indexes: set[int] = set()
    for gold_item in gold_list:
        matched_index = None
        for prediction_index, prediction_item in enumerate(prediction_list):
            if prediction_index in used_prediction_indexes:
                continue
            if score_answers(gold_item, prediction_item):
                matched_index = prediction_index
                break
        if matched_index is None:
            return False
        used_prediction_indexes.add(matched_index)
    return True


def evaluate_submission(
    gold_path: str | Path, prediction_path: str | Path
) -> EvaluationResult:
    # Load both files first so input validation happens before scoring starts.
    gold_records = load_jsonl(gold_path)
    prediction_records = load_jsonl(prediction_path)

    gold_by_id = _index_by_id(gold_records, gold_path)
    prediction_by_id = _index_by_id(prediction_records, prediction_path)

    gold_ids = set(gold_by_id)
    prediction_ids = set(prediction_by_id)

    missing_ids = sorted(gold_ids - prediction_ids)
    unexpected_ids = sorted(prediction_ids - gold_ids)

    correct = 0
    mismatched_ids: list[int] = []

    # Only shared ids can be compared directly; missing ids stay incorrect via the total count.
    for record_id in sorted(gold_ids & prediction_ids):
        gold_answer = gold_by_id[record_id].get("answer")
        prediction_answer = prediction_by_id[record_id].get("answer")
        if score_answers(gold_answer, prediction_answer):
            correct += 1
        else:
            mismatched_ids.append(record_id)

    total = len(gold_records)
    accuracy = correct / total if total else 0.0

    return EvaluationResult(
        accuracy=accuracy,
        correct=correct,
        total=total,
        missing_ids=missing_ids,
        unexpected_ids=unexpected_ids,
        mismatched_ids=mismatched_ids,
    )
