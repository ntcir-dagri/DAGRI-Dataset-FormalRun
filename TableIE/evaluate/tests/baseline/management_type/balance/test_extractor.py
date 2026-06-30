from dagri_subtask1_baseline.management_type.balance.extractor import (
    extract_balance_by_management_type,
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
                    "balance": {
                        "income": 7702,
                        "income_unit": "千円",
                    },
                }
            ]
        }

    def request_json_multimodal(self, **_kwargs):
        return self.request_json(**_kwargs)


def test_extract_balance_by_management_type():
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
    pages = [PDFPage(number=2, text="農業総収入 7,702 千円")]

    actual = extract_balance_by_management_type(
        pages=pages,
        management_types=management_types,
        llm_runtime=_LLMStub(),
    )

    assert "rice" in actual
    assert actual["rice"].income == 7702
