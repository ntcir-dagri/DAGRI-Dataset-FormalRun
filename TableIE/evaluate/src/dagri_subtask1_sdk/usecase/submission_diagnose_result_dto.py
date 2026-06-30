import dataclasses


@dataclasses.dataclass(frozen=True)
class SubmissionDiagnoseResultDTO:
    is_valid: bool
    errors: list[str]
