import pydantic


class CapitalEquipment(pydantic.BaseModel):
    item_name: str | None = None
    amount: int | float | None = None
    specification: str | None = None
    acquisition_cost: int | None = None
    service_life: int | None = None
    depreciation_cost: int | None = None


class CapitalEquipmentList(pydantic.BaseModel):
    items: list[CapitalEquipment] | None = None
