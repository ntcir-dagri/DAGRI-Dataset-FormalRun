import pydantic

from .management_types.balance import Balance
from .management_types.capital_equipment import CapitalEquipmentList
from .management_types.growing_area import GrowingAreaList
from .management_types.premise import Premise


class ManagementType(pydantic.BaseModel):
    id: str
    name: str

    premise: Premise
    growing_area: GrowingAreaList
    balance: Balance
    capital_equipment: CapitalEquipmentList
