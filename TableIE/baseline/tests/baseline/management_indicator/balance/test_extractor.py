from dagri_subtask1_baseline.management_indicator.balance.extractor import (
    extract_indicator_balance,
)
from dagri_subtask1_baseline.shared.pdf_pages import PDFPage
from dagri_subtask1_sdk.domain.management_indicator import ManagementIndicator
from dagri_subtask1_sdk.domain.management_indicators.balance import Balance
from dagri_subtask1_sdk.domain.management_indicators.work_schedule import WorkScheduleList
from dagri_subtask1_sdk.domain.management_indicators.work_technologies import WorkTechnologyList


class _LLMStub:
    def request_json(self, **_kwargs):
        return {
            "items": [
                {
                    "management_indicator_id": "rice",
                    "balance": {
                        "income": 5000,
                        "income_unit": "円",
                    },
                }
            ]
        }

    def request_json_multimodal(self, **_kwargs):
        return self.request_json(**_kwargs)


def test_extract_indicator_balance():
    indicators = [
        ManagementIndicator(
            id="rice",
            crop_name="水稲",
            balance=Balance(),
            work_schedule=WorkScheduleList(term_unit="上下旬", items=None),
            work_technologies=WorkTechnologyList(items=None),
        )
    ]

    actual = extract_indicator_balance(
        pages=[PDFPage(number=1, text="水稲 収支")],
        management_indicators=indicators,
        llm_runtime=_LLMStub(),
    )

    assert actual["rice"].income == 5000
