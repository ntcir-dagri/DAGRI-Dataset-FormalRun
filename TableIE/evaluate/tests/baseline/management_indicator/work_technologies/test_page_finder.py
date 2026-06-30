from dagri_subtask1_baseline.management_indicator.work_technologies.page_finder import (
    find_work_technologies_pages,
)
from dagri_subtask1_baseline.shared.pdf_pages import PDFPage


class _NoLLM:
    def is_available(self) -> bool:
        return False


def test_find_work_technologies_pages_by_keywords_without_llm():
    pages = [
        PDFPage(number=1, text="表紙"),
        PDFPage(number=2, text="水稲 技術体系 作業体系 使用資材"),
    ]

    actual = find_work_technologies_pages(
        pages=pages,
        llm_runtime=_NoLLM(),
        crop_names=["水稲"],
    )

    assert actual == [2]
