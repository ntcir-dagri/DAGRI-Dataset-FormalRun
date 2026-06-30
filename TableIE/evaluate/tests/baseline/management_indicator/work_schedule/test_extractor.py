from dagri_subtask1_baseline.management_indicator.work_schedule.extractor import (
    extract_work_schedule,
    infer_term_unit_from_pages,
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
                    "work_schedule": {
                        "term_unit": "上中下旬",
                        "items": [
                            {
                                "name": "耕起",
                                "period": "4月上旬",
                                "hours": 3.5,
                            }
                        ],
                    },
                }
            ]
        }

    def request_json_multimodal(self, **_kwargs):
        return self.request_json(**_kwargs)


def test_infer_term_unit_from_pages():
    pages = [PDFPage(number=1, text="作業期間は上中下旬で記載")]
    assert infer_term_unit_from_pages(pages) == "上中下旬"


def test_extract_work_schedule():
    indicators = [
        ManagementIndicator(
            id="rice",
            crop_name="水稲",
            balance=Balance(),
            work_schedule=WorkScheduleList(term_unit="上下旬", items=None),
            work_technologies=WorkTechnologyList(items=None),
        )
    ]

    actual = extract_work_schedule(
        pages=[PDFPage(number=1, text="作業期間 月/旬")],
        management_indicators=indicators,
        llm_runtime=_LLMStub(),
    )

    assert actual["rice"].term_unit == "上中下旬"
    assert actual["rice"].items is not None
    assert actual["rice"].items[0].name == "耕起"
