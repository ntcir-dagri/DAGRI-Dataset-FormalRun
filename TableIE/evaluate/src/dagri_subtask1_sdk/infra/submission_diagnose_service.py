from pathlib import Path

import pydantic

from dagri_subtask1_sdk.domain.submission import Submission, SubmissionDataset
from dagri_subtask1_sdk.domain.submission_diagnose_service import (
    SubmissionDiagnoseResult,
    SubmissionDiagnoseService,
)


class FileSystemSubmissionDiagnoseService(SubmissionDiagnoseService):
    def diagnose(
        self,
        submission_file: str,
        subtask1_data_dir: str,
    ) -> SubmissionDiagnoseResult:
        errors: list[str] = []

        submission_path = Path(submission_file)
        dataset_root = Path(subtask1_data_dir)

        parsed_dataset = self._read_submission_dataset(submission_path)
        if isinstance(parsed_dataset, SubmissionDiagnoseResult):
            return parsed_dataset

        expected_keys_or_error = self._collect_expected_keys(dataset_root)
        if isinstance(expected_keys_or_error, SubmissionDiagnoseResult):
            return expected_keys_or_error

        submission_keys = {
            (item.prefecture_name, item.id) for item in parsed_dataset.items
        }
        expected_keys = expected_keys_or_error

        missing_keys = sorted(expected_keys - submission_keys)
        extra_keys = sorted(submission_keys - expected_keys)

        if missing_keys:
            errors.append(f"提出に不足しているサンプルがあります: {missing_keys}")
        if extra_keys:
            errors.append(f"提出に余分なサンプルがあります: {extra_keys}")

        return SubmissionDiagnoseResult(is_valid=len(errors) == 0, errors=errors)

    def _read_submission_dataset(
        self, submission_path: Path
    ) -> SubmissionDataset | SubmissionDiagnoseResult:
        if not submission_path.exists() or not submission_path.is_file():
            return SubmissionDiagnoseResult(
                is_valid=False,
                errors=[f"提出ファイルが見つかりません: {submission_path}"],
            )

        items: list[Submission] = []
        errors: list[str] = []

        try:
            with submission_path.open(encoding="utf-8") as f:
                for line_number, line in enumerate(f, start=1):
                    stripped_line = line.strip()
                    if not stripped_line:
                        continue
                    try:
                        items.append(Submission.model_validate_json(stripped_line))
                    except pydantic.ValidationError as e:
                        for error in e.errors():
                            field_path = ".".join(str(part) for part in error["loc"])
                            errors.append(
                                f"{line_number}行目のJSONが不正です: "
                                f"field={field_path} message={error['msg']}"
                            )
        except OSError as e:
            return SubmissionDiagnoseResult(
                is_valid=False,
                errors=[f"提出ファイルを読み込めませんでした: {e}"],
            )

        if errors:
            return SubmissionDiagnoseResult(is_valid=False, errors=errors)

        return SubmissionDataset(items=items)

    def _collect_expected_keys(
        self, dataset_root: Path
    ) -> set[tuple[str, str]] | SubmissionDiagnoseResult:
        test_dir = dataset_root / "test"
        if not test_dir.exists() or not test_dir.is_dir():
            return SubmissionDiagnoseResult(
                is_valid=False,
                errors=[
                    "データセットディレクトリ内に test ディレクトリが見つかりません: "
                    f"{test_dir}"
                ],
            )

        expected_keys: set[tuple[str, str]] = set()
        for pdf_file in test_dir.rglob("*.pdf"):
            prefecture_name = pdf_file.parent.name
            file_id = pdf_file.stem
            expected_keys.add((prefecture_name, file_id))

        return expected_keys
