from dagri_subtask1_baseline.management_type.capital_equipment.extractor import (
    extract_capital_equipment_by_management_type,
)
from dagri_subtask1_baseline.shared.pdf_pages import PDFPage
from dagri_subtask1_sdk.domain.management_type import ManagementType
from dagri_subtask1_sdk.domain.management_types.balance import Balance
from dagri_subtask1_sdk.domain.management_types.capital_equipment import CapitalEquipmentList
from dagri_subtask1_sdk.domain.management_types.growing_area import GrowingAreaList
from dagri_subtask1_sdk.domain.management_types.premise import Premise


class _LLMStub:
    def request_json(self, **_kwargs):
        return {
            "items": [
                {
                    "management_type_id": "rice",
                    "capital_equipment": {
                        "items": [
                            {
                                "item_name": "トラクター",
                                "amount": 1,
                            }
                        ]
                    },
                }
            ]
        }

    def request_json_multimodal(self, **_kwargs):
        return self.request_json(**_kwargs)


def test_extract_capital_equipment_by_management_type():
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
    pages = [PDFPage(number=2, text="トラクター 1台")]

    actual = extract_capital_equipment_by_management_type(
        pages=pages,
        management_types=management_types,
        llm_runtime=_LLMStub(),
    )

    assert "rice" in actual
    assert actual["rice"].items is not None
    assert actual["rice"].items[0].item_name == "トラクター"


class _LLMDecimalStub:
    def request_json(self, **_kwargs):
        return {
            "items": [
                {
                    "management_type_id": "rice",
                    "capital_equipment": {
                        "items": [
                            {
                                "item_name": "播種機",
                                "amount": 1.5,
                            }
                        ]
                    },
                }
            ]
        }

    def request_json_multimodal(self, **_kwargs):
        return self.request_json(**_kwargs)


def test_extract_capital_equipment_by_management_type_accepts_decimal_amount():
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
    pages = [PDFPage(number=2, text="播種機 1.5台")]

    actual = extract_capital_equipment_by_management_type(
        pages=pages,
        management_types=management_types,
        llm_runtime=_LLMDecimalStub(),
    )

    assert "rice" in actual
    assert actual["rice"].items is not None
    assert actual["rice"].items[0].amount == 1.5
