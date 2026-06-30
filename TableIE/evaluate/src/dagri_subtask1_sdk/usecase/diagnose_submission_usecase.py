from pathlib import Path

from dagri_subtask1_sdk.domain.submission_diagnose_service import (
    SubmissionDiagnoseService,
)

from .submission_diagnose_result_dto import SubmissionDiagnoseResultDTO


class DiagnoseSubmissionUsecase:
    def __init__(self, submission_diagnose_service: SubmissionDiagnoseService) -> None:
        self._submission_diagnose_service = submission_diagnose_service

    def execute(
        self,
        submission_file_path: str | Path,
        subtask1_data_dir: str | Path,
    ) -> SubmissionDiagnoseResultDTO:
        diagnose_result = self._submission_diagnose_service.diagnose(
            submission_file=str(submission_file_path),
            subtask1_data_dir=str(subtask1_data_dir),
        )
        return SubmissionDiagnoseResultDTO(
            is_valid=diagnose_result.is_valid,
            errors=diagnose_result.errors,
        )
