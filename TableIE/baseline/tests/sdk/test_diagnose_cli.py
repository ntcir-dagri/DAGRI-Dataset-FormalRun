import json
import subprocess
import sys


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


def test_cli_prints_ok_when_submission_is_valid(tmp_path):
    test_dir = tmp_path / "dataset" / "test" / "tokyo"
    test_dir.mkdir(parents=True)
    (test_dir / "a.pdf").write_bytes(b"%PDF")

    submission_file = tmp_path / "submission.jsonl"
    submission_file.write_text(
        json.dumps(_minimal_submission("tokyo", "a"), ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    cmd = [
        sys.executable,
        "-m",
        "dagri_subtask1_sdk.main.diagnose",
        "--submission",
        str(submission_file),
        "--data-dir",
        str(tmp_path / "dataset"),
    ]
    completed = subprocess.run(cmd, check=False, capture_output=True, text=True)

    assert completed.returncode == 0
    assert completed.stdout.strip() == "OK"


def test_cli_prints_errors_when_submission_has_problems(tmp_path):
    test_dir = tmp_path / "dataset" / "test" / "tokyo"
    test_dir.mkdir(parents=True)
    (test_dir / "a.pdf").write_bytes(b"%PDF")

    submission_file = tmp_path / "submission.jsonl"
    submission_file.write_text(
        json.dumps(_minimal_submission("tokyo", "unknown-id"), ensure_ascii=False)
        + "\n",
        encoding="utf-8",
    )

    cmd = [
        sys.executable,
        "-m",
        "dagri_subtask1_sdk.main.diagnose",
        "-s",
        str(submission_file),
        "-d",
        str(tmp_path / "dataset"),
    ]
    completed = subprocess.run(cmd, check=False, capture_output=True, text=True)

    assert completed.returncode == 1
    assert "不足" in completed.stdout
    assert "余分" in completed.stdout
