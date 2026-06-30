import pydantic

from .eval_dataset import EvalDataset
from .management_type import ManagementType
from .management_indicator import ManagementIndicator


class Submission(pydantic.BaseModel):
    prefecture_name: str
    id: str
    management_types: list[ManagementType]
    management_indicators: list[ManagementIndicator]


class SubmissionDataset(pydantic.BaseModel):
    items: list[Submission]

    def validate_item_keys(
        self, eval_dataset: EvalDataset
    ) -> tuple[bool, list[tuple[str, str]]]:
        submission_keys = {(item.prefecture_name, item.id) for item in self.items}
        eval_keys = {(item.prefecture_name, item.id) for item in eval_dataset.items}
        missing_or_extra_keys = sorted(submission_keys ^ eval_keys)

        return len(missing_or_extra_keys) == 0, missing_or_extra_keys
