from dagri_subtask1_baseline.management_indicator.work_schedule.page_finder import (
    find_work_schedule_pages,
)
from dagri_subtask1_baseline.shared.pdf_pages import PDFPage


class _NoLLM:
    def is_available(self) -> bool:
        return False


def test_find_work_schedule_pages_by_keywords_without_llm():
    pages = [
        PDFPage(number=1, text="表紙"),
        PDFPage(number=2, text="水稲 作業期間 月/旬 ガント"),
    ]

    actual = find_work_schedule_pages(
        pages=pages,
        llm_runtime=_NoLLM(),
        crop_names=["水稲"],
    )

    assert actual == [2]
