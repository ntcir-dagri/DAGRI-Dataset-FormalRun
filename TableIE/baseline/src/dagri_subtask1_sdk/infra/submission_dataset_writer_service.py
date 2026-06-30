from pathlib import Path

from dagri_subtask1_sdk.domain.submission import SubmissionDataset
from dagri_subtask1_sdk.domain.submission_dataset_writer_service import (
    SubmissionDatasetWriterService,
)


class JsonlSubmissionDatasetWriterService(SubmissionDatasetWriterService):
    def write(
        self, submission_dataset: SubmissionDataset, output_file_path: str
    ) -> None:
        output_path = Path(output_file_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with output_path.open("w", encoding="utf-8") as f:
            for item in submission_dataset.items:
                print(item.model_dump_json(ensure_ascii=False), file=f)
