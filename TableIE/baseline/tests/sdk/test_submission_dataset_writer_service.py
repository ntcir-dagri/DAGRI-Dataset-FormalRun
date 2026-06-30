import json

from dagri_subtask1_sdk.domain.submission import SubmissionDataset
from dagri_subtask1_sdk.infra.submission_dataset_writer_service import (
    JsonlSubmissionDatasetWriterService,
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


def test_write_outputs_submission_dataset_as_jsonl(tmp_path):
    dataset = SubmissionDataset.model_validate(
        {
            "items": [
                _minimal_submission("tokyo", "a"),
                _minimal_submission("osaka", "b"),
            ]
        }
    )
    output_file = tmp_path / "output" / "submission.jsonl"

    writer = JsonlSubmissionDatasetWriterService()
    writer.write(submission_dataset=dataset, output_file_path=str(output_file))

    lines = output_file.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 2

    row1 = json.loads(lines[0])
    row2 = json.loads(lines[1])
    assert row1["prefecture_name"] == "tokyo"
    assert row1["id"] == "a"
    assert row2["prefecture_name"] == "osaka"
    assert row2["id"] == "b"


def test_write_keeps_decimal_capital_equipment_amount(tmp_path):
    dataset = SubmissionDataset.model_validate(
        {
            "items": [
                {
                    "prefecture_name": "tokyo",
                    "id": "a",
                    "management_types": [
                        {
                            "id": "mt-1",
                            "name": "type-a",
                            "premise": {},
                            "growing_area": {"items": None},
                            "balance": {},
                            "capital_equipment": {
                                "items": [{"item_name": "播種機", "amount": 1.5}]
                            },
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
            ]
        }
    )
    output_file = tmp_path / "output" / "submission.jsonl"

    writer = JsonlSubmissionDatasetWriterService()
    writer.write(submission_dataset=dataset, output_file_path=str(output_file))

    row = json.loads(output_file.read_text(encoding="utf-8").strip())
    amount = row["management_types"][0]["capital_equipment"]["items"][0]["amount"]
    assert amount == 1.5
