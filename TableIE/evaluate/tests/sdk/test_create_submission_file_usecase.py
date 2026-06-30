from pathlib import Path

from dagri_subtask1_sdk.domain.submission import SubmissionDataset
from dagri_subtask1_sdk.domain.submission_dataset_writer_service import (
    SubmissionDatasetWriterService,
)
from dagri_subtask1_sdk.usecase import CreateSubmissionFileUsecase


class DummySubmissionDatasetWriterService(SubmissionDatasetWriterService):
    def __init__(self) -> None:
        self.called_with: tuple[SubmissionDataset, str] | None = None

    def write(self, submission_dataset: SubmissionDataset, output_file_path: str) -> None:
        self.called_with = (submission_dataset, output_file_path)


def test_execute_delegates_to_writer_service():
    writer = DummySubmissionDatasetWriterService()
    usecase = CreateSubmissionFileUsecase(submission_dataset_writer_service=writer)

    dataset = SubmissionDataset.model_validate({"items": []})
    output_path = Path("/tmp/submission.jsonl")

    usecase.execute(submission_dataset=dataset, output_file_path=output_path)

    assert writer.called_with is not None
    called_dataset, called_path = writer.called_with
    assert called_dataset == dataset
    assert called_path == str(output_path)
