import enum
from typing import Literal

import pydantic


class WorkSchedulePeriod(enum.Enum):
    EARLY_JANUARY = "1月上旬"
    MID_JANUARY = "1月中旬"
    LATE_JANUARY = "1月下旬"
    EARLY_FEBRUARY = "2月上旬"
    MID_FEBRUARY = "2月中旬"
    LATE_FEBRUARY = "2月下旬"
    EARLY_MARCH = "3月上旬"
    MID_MARCH = "3月中旬"
    LATE_MARCH = "3月下旬"
    EARLY_APRIL = "4月上旬"
    MID_APRIL = "4月中旬"
    LATE_APRIL = "4月下旬"
    EARLY_MAY = "5月上旬"
    MID_MAY = "5月中旬"
    LATE_MAY = "5月下旬"
    EARLY_JUNE = "6月上旬"
    MID_JUNE = "6月中旬"
    LATE_JUNE = "6月下旬"
    EARLY_JULY = "7月上旬"
    MID_JULY = "7月中旬"
    LATE_JULY = "7月下旬"
    EARLY_AUGUST = "8月上旬"
    MID_AUGUST = "8月中旬"
    LATE_AUGUST = "8月下旬"
    EARLY_SEPTEMBER = "9月上旬"
    MID_SEPTEMBER = "9月中旬"
    LATE_SEPTEMBER = "9月下旬"
    EARLY_OCTOBER = "10月上旬"
    MID_OCTOBER = "10月中旬"
    LATE_OCTOBER = "10月下旬"
    EARLY_NOVEMBER = "11月上旬"
    MID_NOVEMBER = "11月中旬"
    LATE_NOVEMBER = "11月下旬"
    EARLY_DECEMBER = "12月上旬"
    MID_DECEMBER = "12月中旬"
    LATE_DECEMBER = "12月下旬"


class WorkSchedule(pydantic.BaseModel):
    name: str | None
    period: WorkSchedulePeriod | None
    hours: float | None


class WorkScheduleList(pydantic.BaseModel):
    term_unit: Literal["上下旬", "上中下旬"]
    items: list[WorkSchedule] | None
