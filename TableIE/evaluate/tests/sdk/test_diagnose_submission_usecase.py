from pathlib import Path

from dagri_subtask1_sdk.domain.submission_diagnose_service import (
    SubmissionDiagnoseResult,
    SubmissionDiagnoseService,
)
from dagri_subtask1_sdk.usecase import (
    DiagnoseSubmissionUsecase,
    SubmissionDiagnoseResultDTO,
)


class DummySubmissionDiagnoseService(SubmissionDiagnoseService):
    def __init__(self, result: SubmissionDiagnoseResult) -> None:
        self._result = result
        self.called_with: tuple[str, str] | None = None

    def diagnose(
        self,
        submission_file: str,
        subtask1_data_dir: str,
    ) -> SubmissionDiagnoseResult:
        self.called_with = (submission_file, subtask1_data_dir)
        return self._result


def test_execute_delegates_to_service_and_returns_result():
    domain_result = SubmissionDiagnoseResult(is_valid=False, errors=["dummy error"])
    service = DummySubmissionDiagnoseService(result=domain_result)
    usecase = DiagnoseSubmissionUsecase(submission_diagnose_service=service)

    submission_path = Path("/tmp/submission.jsonl")
    dataset_dir = Path("/tmp/subtask1_data")

    result = usecase.execute(
        submission_file_path=submission_path,
        subtask1_data_dir=dataset_dir,
    )

    assert isinstance(result, SubmissionDiagnoseResultDTO)
    assert result.is_valid is domain_result.is_valid
    assert result.errors == domain_result.errors
    assert service.called_with == (str(submission_path), str(dataset_dir))
