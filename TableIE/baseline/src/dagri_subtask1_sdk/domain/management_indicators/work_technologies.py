import pydantic


class WorkTechnologyEquipment(pydantic.BaseModel):
    name: str | None = None
    hour: float | None = None


class WorkTechnologyMaterial(pydantic.BaseModel):
    name: str | None = None
    usage: str | None = None
    usage_unit: str | None = None


class WorkTechnology(pydantic.BaseModel):
    name: str | None = None
    description: str | None = None
    eqiupments: list[WorkTechnologyEquipment] | None = None
    materials: list[WorkTechnologyMaterial] | None = None
    number_of_workers: int | None = None
    total_number_of_hours: float | None = None
    cost: int | None = None
    note: str | None = None


class WorkTechnologyList(pydantic.BaseModel):
    items: list[WorkTechnology] | None = None
