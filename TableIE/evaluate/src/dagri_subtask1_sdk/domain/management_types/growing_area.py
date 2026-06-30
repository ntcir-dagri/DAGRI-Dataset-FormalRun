import pydantic


class GrowingArea(pydantic.BaseModel):
    crop_name: str | None = None
    cultivars: list[str] | None = None
    area: int | None = None
    area_unit: str | None = None


class GrowingAreaList(pydantic.BaseModel):
    items: list[GrowingArea] | None = None
