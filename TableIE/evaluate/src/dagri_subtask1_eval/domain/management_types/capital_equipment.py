import pydantic


class CapitalEquipment(pydantic.BaseModel):
    item_name: str | None = None
    amount: float | None = None
    specification: str | None = None
    acquisition_cost: int | float | None = None
    service_life: int | float | None = None
    depreciation_cost: int | float | None = None


class CapitalEquipmentList(pydantic.BaseModel):
    items: list[CapitalEquipment] | None = None
