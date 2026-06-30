import pydantic

from .management_indicators.balance import Balance
from .management_indicators.work_schedule import WorkScheduleList
from .management_indicators.work_technologies import WorkTechnologyList


class ManagementIndicator(pydantic.BaseModel):
    id: str
    crop_name: str
    balance: Balance
    work_schedule: WorkScheduleList
    work_technologies: WorkTechnologyList
