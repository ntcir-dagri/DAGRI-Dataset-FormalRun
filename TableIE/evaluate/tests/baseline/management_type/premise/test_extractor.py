from dagri_subtask1_baseline.management_type.premise.extractor import (
    extract_premise_by_management_type,
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
                    "premise": {
                        "prefecture_name": "tokyo",
                        "labors": 2.5,
                    },
                }
            ]
        }

    def request_json_multimodal(self, **_kwargs):
        return self.request_json(**_kwargs)


def test_extract_premise_by_management_type():
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
    pages = [PDFPage(number=2, text="前提\n自家労働 2.5人")]

    actual = extract_premise_by_management_type(
        pages=pages,
        management_types=management_types,
        llm_runtime=_LLMStub(),
    )

    assert "rice" in actual
    assert actual["rice"].prefecture_name == "tokyo"
    assert actual["rice"].labors == 2.5
