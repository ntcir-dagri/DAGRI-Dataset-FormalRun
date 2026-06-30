import pydantic


class Premise(pydantic.BaseModel):
    prefecture_name: str | None = pydantic.Field(default=None)
    area_name: str | None = pydantic.Field(default=None)
    crop_names: list[str] | None = pydantic.Field(default=None)
    cultivate_land: int | float | None = pydantic.Field(default=None)
    cultivate_land_unit: str | None = pydantic.Field(default=None)
    borrowed_cultivate_land: int | float | None = pydantic.Field(default=None)
    owned_cultivate_land: int | float | None = pydantic.Field(default=None)
    labor_raw: str | None = pydantic.Field(default=None)
    labors: float | None = pydantic.Field(default=None)
    total_income: int | float | None = pydantic.Field(default=None)
    total_labor_hours: float | None = pydantic.Field(default=None)
    note: str | None = pydantic.Field(default=None)
