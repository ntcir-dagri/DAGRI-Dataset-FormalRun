from pathlib import Path

import pytest

from dagri_subtask1_eval.infra.dataset_reader_error import DatasetValidationError
from dagri_subtask1_eval.infra.submission_dataset_reader import SubmissionDatasetReader


def test_read_returns_submission_dataset_from_jsonl() -> None:
    reader = SubmissionDatasetReader()

    dataset = reader.read(Path("examples/test_groundtruth.jsonl"))

    assert len(dataset.items) == 7

    first_item = dataset.items[0]
    assert first_item.prefecture_name == "nagasaki"
    assert first_item.id == "1727423373"
    assert len(first_item.management_types) == 1
    assert first_item.management_types[0].id == "onion"
    assert first_item.management_types[0].growing_area.items[0].area == 100
    assert len(first_item.management_indicators) == 1
    assert first_item.management_indicators[0].crop_name == "たまねぎ（加工・業務用）"
    assert first_item.management_indicators[0].work_schedule.items[0].period.value == "1月上旬"


def test_read_skips_blank_lines(tmp_path: Path) -> None:
    dataset_file = tmp_path / "submission.jsonl"
    dataset_file.write_text(
        '\n{"prefecture_name":"tokyo","id":"1","management_types":[],"management_indicators":[]}\n\n',
        encoding="utf-8",
    )

    reader = SubmissionDatasetReader()

    dataset = reader.read(dataset_file)

    assert len(dataset.items) == 1
    assert dataset.items[0].prefecture_name == "tokyo"


def test_read_collects_all_validation_issues_before_raising() -> None:
    reader = SubmissionDatasetReader()
    dataset_file = Path("tests/data_invalid_submission.jsonl")

    with pytest.raises(DatasetValidationError) as exc_info:
        reader.read(dataset_file)

    issues = exc_info.value.issues

    assert len(issues) == 3
    assert issues[0].line_number == 1
    assert issues[0].field_path == ("management_types",)
    assert issues[1].line_number == 1
    assert issues[1].field_path == ("management_indicators",)
    assert issues[2].line_number == 2
    assert issues[2].field_path == ("id",)


def test_read_accepts_float_numeric_fields(tmp_path: Path) -> None:
    dataset_file = tmp_path / "submission_float.jsonl"
    dataset_file.write_text(
        '{"prefecture_name":"tokyo","id":"1","management_types":[{"id":"onion","name":"たまねぎ","premise":{"cultivate_land":100.5,"borrowed_cultivate_land":20.25,"owned_cultivate_land":80.25,"total_income":1000.75},"growing_area":{"items":[{"crop_name":"たまねぎ","area":10.5}]},"balance":{},"capital_equipment":{"items":[]}}],"management_indicators":[{"id":"onion","crop_name":"たまねぎ","balance":{},"work_schedule":{"term_unit":"上中下旬","items":[]},"work_technologies":{"items":[{"name":"播種","number_of_workers":2.5,"cost":1000.25}]}}]}\n',
        encoding="utf-8",
    )

    reader = SubmissionDatasetReader()
    dataset = reader.read(dataset_file)

    first_item = dataset.items[0]
    assert first_item.management_types[0].premise.cultivate_land == 100.5
    assert first_item.management_types[0].growing_area.items[0].area == 10.5
    assert first_item.management_indicators[0].work_technologies.items[0].number_of_workers == 2.5
