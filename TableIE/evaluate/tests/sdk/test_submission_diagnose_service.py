import json

from dagri_subtask1_sdk.infra.submission_diagnose_service import (
    FileSystemSubmissionDiagnoseService,
)


def _minimal_submission(prefecture_name: str, file_id: str) -> dict:
    return {
        "prefecture_name": prefecture_name,
        "id": file_id,
        "management_types": [
            {
                "id": "mt-1",
                "name": "type-a",
                "premise": {},
                "growing_area": {"items": None},
                "balance": {},
                "capital_equipment": {"items": None},
            }
        ],
        "management_indicators": [
            {
                "id": "mi-1",
                "crop_name": "crop-a",
                "balance": {},
                "work_schedule": {"term_unit": "上下旬", "items": None},
                "work_technologies": {"items": None},
            }
        ],
    }


def test_diagnose_returns_valid_for_matching_submission(tmp_path):
    test_dir = tmp_path / "dataset" / "test"
    (test_dir / "tokyo").mkdir(parents=True)
    (test_dir / "tokyo" / "a.pdf").write_bytes(b"%PDF")
    (test_dir / "osaka").mkdir(parents=True)
    (test_dir / "osaka" / "b.pdf").write_bytes(b"%PDF")

    submission_file = tmp_path / "submission.jsonl"
    lines = [
        json.dumps(_minimal_submission("tokyo", "a"), ensure_ascii=False),
        json.dumps(_minimal_submission("osaka", "b"), ensure_ascii=False),
    ]
    submission_file.write_text("\n".join(lines) + "\n", encoding="utf-8")

    service = FileSystemSubmissionDiagnoseService()
    result = service.diagnose(
        submission_file=str(submission_file),
        subtask1_data_dir=str(tmp_path / "dataset"),
    )

    assert result.is_valid is True
    assert result.errors == []


def test_diagnose_returns_error_for_invalid_jsonl_schema(tmp_path):
    (tmp_path / "dataset" / "test" / "tokyo").mkdir(parents=True)
    (tmp_path / "dataset" / "test" / "tokyo" / "a.pdf").write_bytes(b"%PDF")

    submission_file = tmp_path / "submission.jsonl"
    # required field "id" is missing.
    submission_file.write_text(
        json.dumps(
            {
                "prefecture_name": "tokyo",
                "management_types": [],
                "management_indicators": [],
            },
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )

    service = FileSystemSubmissionDiagnoseService()
    result = service.diagnose(
        submission_file=str(submission_file),
        subtask1_data_dir=str(tmp_path / "dataset"),
    )

    assert result.is_valid is False
    assert len(result.errors) == 1
    assert "1行目のJSONが不正です" in result.errors[0]


def test_diagnose_returns_error_for_missing_and_extra_keys(tmp_path):
    test_dir = tmp_path / "dataset" / "test"
    (test_dir / "tokyo").mkdir(parents=True)
    (test_dir / "tokyo" / "a.pdf").write_bytes(b"%PDF")
    (test_dir / "osaka").mkdir(parents=True)
    (test_dir / "osaka" / "b.pdf").write_bytes(b"%PDF")

    submission_file = tmp_path / "submission.jsonl"
    lines = [
        json.dumps(_minimal_submission("tokyo", "a"), ensure_ascii=False),
        json.dumps(_minimal_submission("kyoto", "c"), ensure_ascii=False),
    ]
    submission_file.write_text("\n".join(lines) + "\n", encoding="utf-8")

    service = FileSystemSubmissionDiagnoseService()
    result = service.diagnose(
        submission_file=str(submission_file),
        subtask1_data_dir=str(tmp_path / "dataset"),
    )

    assert result.is_valid is False
    assert len(result.errors) == 2
    assert "不足" in result.errors[0]
    assert "余分" in result.errors[1]


def test_diagnose_accepts_decimal_capital_equipment_amount(tmp_path):
    (tmp_path / "dataset" / "test" / "tokyo").mkdir(parents=True)
    (tmp_path / "dataset" / "test" / "tokyo" / "a.pdf").write_bytes(b"%PDF")

    submission_file = tmp_path / "submission.jsonl"
    payload = _minimal_submission("tokyo", "a")
    payload["management_types"][0]["capital_equipment"] = {
        "items": [{"item_name": "播種機", "amount": 1.5}]
    }
    submission_file.write_text(
        json.dumps(payload, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    service = FileSystemSubmissionDiagnoseService()
    result = service.diagnose(
        submission_file=str(submission_file),
        subtask1_data_dir=str(tmp_path / "dataset"),
    )

    assert result.is_valid is True
    assert result.errors == []
