from pathlib import Path

import pydantic

from dagri_subtask1_eval.domain.submission import Submission, SubmissionDataset
from dagri_subtask1_eval.infra.dataset_reader_error import (
    DatasetValidationError,
    DatasetValidationIssue,
)


class SubmissionDatasetReader:
    def read(self, file_path: str | Path) -> SubmissionDataset:
        path = Path(file_path)
        items: list[Submission] = []
        issues: list[DatasetValidationIssue] = []

        with path.open(encoding="utf-8") as f:
            for line_number, line in enumerate(f, start=1):
                stripped_line = line.strip()
                if not stripped_line:
                    continue
                try:
                    items.append(Submission.model_validate_json(stripped_line))
                except pydantic.ValidationError as e:
                    issues.extend(
                        [
                            DatasetValidationIssue(
                                line_number=line_number,
                                field_path=tuple(error["loc"]),
                                message=error["msg"],
                                input_value=error.get("input"),
                            )
                            for error in e.errors()
                        ]
                    )

        if issues:
            raise DatasetValidationError(issues)

        return SubmissionDataset(items=items)
