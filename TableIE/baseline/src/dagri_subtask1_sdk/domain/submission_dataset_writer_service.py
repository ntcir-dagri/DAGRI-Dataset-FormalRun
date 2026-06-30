import abc

from .submission import SubmissionDataset


class SubmissionDatasetWriterService(abc.ABC):
    @abc.abstractmethod
    def write(
        self, submission_dataset: SubmissionDataset, output_file_path: str
    ) -> None:
        """SubmissionDataset を JSONL 形式でファイルに書き出します。"""
