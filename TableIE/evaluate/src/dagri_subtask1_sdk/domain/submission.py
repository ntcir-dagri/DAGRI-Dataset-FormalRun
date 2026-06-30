import pydantic

from .management_indicator import ManagementIndicator
from .management_type import ManagementType


class Submission(pydantic.BaseModel):
    prefecture_name: str
    id: str
    management_types: list[ManagementType]
    management_indicators: list[ManagementIndicator]


class SubmissionDataset(pydantic.BaseModel):
    items: list[Submission]
