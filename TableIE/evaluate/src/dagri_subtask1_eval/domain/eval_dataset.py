import pydantic

from .management_type import ManagementType
from .management_indicator import ManagementIndicator


class EvalData(pydantic.BaseModel):
    prefecture_name: str
    id: str
    management_types: list[ManagementType]
    management_indicators: list[ManagementIndicator]


class EvalDataset(pydantic.BaseModel):
    items: list[EvalData]
