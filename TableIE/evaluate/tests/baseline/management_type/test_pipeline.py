from dagri_subtask1_baseline.management_type import pipeline
from dagri_subtask1_baseline.shared.pdf_pages import PDFPage
from dagri_subtask1_sdk.domain.management_type import ManagementType
from dagri_subtask1_sdk.domain.management_types.balance import Balance
from dagri_subtask1_sdk.domain.management_types.capital_equipment import CapitalEquipmentList
from dagri_subtask1_sdk.domain.management_types.growing_area import GrowingArea, GrowingAreaList
from dagri_subtask1_sdk.domain.management_types.premise import Premise


class _NoLLM:
    def is_available(self) -> bool:
        return False


def test_pipeline_sets_fields_by_step(monkeypatch):
    management_types = [
        ManagementType(
            id="rice",
            name="水稲",
            premise=Premise(),
            growing_area=GrowingAreaList(items=None),
            balance=Balance(),
            capital_equipment=CapitalEquipmentList(items=None),
        )
    ]

    monkeypatch.setattr(pipeline, "extract_management_type_names", lambda **_kwargs: management_types)
    monkeypatch.setattr(pipeline, "find_premise_pages", lambda **_kwargs: [1])
    monkeypatch.setattr(
        pipeline,
        "extract_premise_by_management_type",
        lambda **_kwargs: {"rice": Premise(prefecture_name="tokyo")},
    )
    monkeypatch.setattr(pipeline, "find_growing_area_pages", lambda **_kwargs: [2])
    monkeypatch.setattr(
        pipeline,
        "extract_growing_area_by_management_type",
        lambda **_kwargs: {
            "rice": GrowingAreaList(items=[GrowingArea(crop_name="水稲", area=10, area_unit="a")])
        },
    )
    monkeypatch.setattr(pipeline, "find_balance_pages", lambda **_kwargs: [3])
    monkeypatch.setattr(
        pipeline,
        "extract_balance_by_management_type",
        lambda **_kwargs: {"rice": Balance(income=1000)},
    )
    monkeypatch.setattr(pipeline, "find_capital_equipment_pages", lambda **_kwargs: [4])
    monkeypatch.setattr(
        pipeline,
        "extract_capital_equipment_by_management_type",
        lambda **_kwargs: {
            "rice": CapitalEquipmentList(items=[])
        },
    )

    result = pipeline.extract_management_types(
        pages=[PDFPage(number=1, text="dummy")],
        llm_runtime=_NoLLM(),
    )

    assert len(result) == 1
    assert result[0].premise.prefecture_name == "tokyo"
    assert result[0].growing_area.items is not None
    assert result[0].growing_area.items[0].crop_name == "水稲"
    assert result[0].balance.income == 1000
    assert result[0].capital_equipment.items == []
