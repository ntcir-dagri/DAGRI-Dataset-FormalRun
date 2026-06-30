from dataclasses import dataclass


@dataclass(frozen=True)
class DatasetValidationIssue:
    line_number: int
    field_path: tuple[str | int, ...]
    message: str
    input_value: object


class DatasetValidationError(Exception):
    def __init__(self, issues: list[DatasetValidationIssue]) -> None:
        self.issues = issues
        super().__init__(self._build_message())

    def _build_message(self) -> str:
        details = ", ".join(
            (
                f"line={issue.line_number}"
                f" path={'.'.join(str(part) for part in issue.field_path)}"
                f" message={issue.message}"
            )
            for issue in self.issues
        )
        return f"データセットに不正な値があります: {details}"
