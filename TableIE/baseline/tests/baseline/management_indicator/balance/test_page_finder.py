from dagri_subtask1_baseline.management_indicator.balance.page_finder import (
    find_indicator_balance_pages,
)
from dagri_subtask1_baseline.shared.pdf_pages import PDFPage


class _NoLLM:
    def is_available(self) -> bool:
        return False


def test_find_indicator_balance_pages_by_keywords_without_llm():
    pages = [
        PDFPage(number=1, text="表紙"),
        PDFPage(number=2, text="水稲 収支 10a当たり"),
        PDFPage(number=3, text="類型全体の収支"),
    ]

    actual = find_indicator_balance_pages(
        pages=pages,
        llm_runtime=_NoLLM(),
        crop_names=["水稲"],
    )

    assert actual == [2]
