from dagri_subtask1_baseline.management_indicator.work_technologies.extractor import (
    extract_work_technologies,
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
                    "work_technologies": {
                        "items": [
                            {
                                "name": "耕起",
                                "description": "トラクターで耕起",
                            }
                        ]
                    },
                }
            ]
        }

    def request_json_multimodal(self, **_kwargs):
        return self.request_json(**_kwargs)


def test_extract_work_technologies():
    indicators = [
        ManagementIndicator(
            id="rice",
            crop_name="水稲",
            balance=Balance(),
            work_schedule=WorkScheduleList(term_unit="上下旬", items=None),
            work_technologies=WorkTechnologyList(items=None),
        )
    ]

    actual = extract_work_technologies(
        pages=[PDFPage(number=1, text="技術体系")],
        management_indicators=indicators,
        llm_runtime=_LLMStub(),
    )

    assert actual["rice"].items is not None
    assert actual["rice"].items[0].name == "耕起"
