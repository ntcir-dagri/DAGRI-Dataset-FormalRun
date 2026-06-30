from dagri_subtask1_baseline.management_indicator import pipeline
from dagri_subtask1_baseline.shared.pdf_pages import PDFPage
from dagri_subtask1_sdk.domain.management_type import ManagementType
from dagri_subtask1_sdk.domain.management_types.balance import Balance
from dagri_subtask1_sdk.domain.management_types.capital_equipment import CapitalEquipmentList
from dagri_subtask1_sdk.domain.management_types.growing_area import GrowingArea, GrowingAreaList
from dagri_subtask1_sdk.domain.management_types.premise import Premise
from dagri_subtask1_sdk.domain.management_indicators.balance import Balance as IndicatorBalance
from dagri_subtask1_sdk.domain.management_indicators.work_schedule import WorkScheduleList
from dagri_subtask1_sdk.domain.management_indicators.work_technologies import WorkTechnologyList


class _NoLLM:
    def is_available(self) -> bool:
        return False


def test_pipeline_builds_indicators_from_growing_area_and_sets_fields(monkeypatch):
    management_types = [
        ManagementType(
            id="mt-1",
            name="水稲類型",
            premise=Premise(),
            growing_area=GrowingAreaList(
                items=[
                    GrowingArea(crop_name="水稲", area=10, area_unit="a"),
                    GrowingArea(crop_name="麦", area=5, area_unit="a"),
                ]
            ),
            balance=Balance(),
            capital_equipment=CapitalEquipmentList(items=None),
        )
    ]

    monkeypatch.setattr(pipeline, "find_indicator_balance_pages", lambda **_kwargs: [1])
    def _extract_balance_stub(**kwargs):
        indicator_id = kwargs["management_indicators"][0].id
        return {indicator_id: IndicatorBalance(income=100)}

    monkeypatch.setattr(
        pipeline,
        "extract_indicator_balance",
        _extract_balance_stub,
    )
    monkeypatch.setattr(pipeline, "find_work_technologies_pages", lambda **_kwargs: [2])
    def _extract_work_technologies_stub(**kwargs):
        indicator_id = kwargs["management_indicators"][0].id
        return {indicator_id: WorkTechnologyList(items=[])}

    monkeypatch.setattr(
        pipeline,
        "extract_work_technologies",
        _extract_work_technologies_stub,
    )
    monkeypatch.setattr(pipeline, "find_work_schedule_pages", lambda **_kwargs: [3])
    def _extract_work_schedule_stub(**kwargs):
        indicator_id = kwargs["management_indicators"][0].id
        return {indicator_id: WorkScheduleList(term_unit="上下旬", items=[])}

    monkeypatch.setattr(
        pipeline,
        "extract_work_schedule",
        _extract_work_schedule_stub,
    )

    actual = pipeline.extract_management_indicators(
        pages=[PDFPage(number=1, text="dummy")],
        management_types=management_types,
        llm_runtime=_NoLLM(),
    )

    assert len(actual) == 2
    assert [item.crop_name for item in actual] == ["水稲", "麦"]
    assert actual[0].balance.income == 100
    assert actual[0].work_technologies.items == []
    assert actual[0].work_schedule.items == []


def test_pipeline_returns_empty_when_no_crop_names():
    management_types = [
        ManagementType(
            id="mt-1",
            name="空類型",
            premise=Premise(),
            growing_area=GrowingAreaList(items=None),
            balance=Balance(),
            capital_equipment=CapitalEquipmentList(items=None),
        )
    ]

    actual = pipeline.extract_management_indicators(
        pages=[PDFPage(number=1, text="dummy")],
        management_types=management_types,
        llm_runtime=_NoLLM(),
    )

    assert actual == []
