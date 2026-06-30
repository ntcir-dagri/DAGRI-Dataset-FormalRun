from pathlib import Path

from dagri_subtask1_sdk.domain.submission import SubmissionDataset
from dagri_subtask1_sdk.domain.submission_dataset_writer_service import (
    SubmissionDatasetWriterService,
)


class CreateSubmissionFileUsecase:
    def __init__(
        self, submission_dataset_writer_service: SubmissionDatasetWriterService
    ):
        self._submission_dataset_writer_service = submission_dataset_writer_service

    def execute(
        self,
        submission_dataset: SubmissionDataset,
        output_file_path: str | Path,
    ) -> None:
        self._submission_dataset_writer_service.write(
            submission_dataset=submission_dataset,
            output_file_path=str(output_file_path),
        )
