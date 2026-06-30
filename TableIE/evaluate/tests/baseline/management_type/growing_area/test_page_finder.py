from dagri_subtask1_baseline.management_type.growing_area.page_finder import (
    find_growing_area_pages,
)
from dagri_subtask1_baseline.shared.pdf_pages import PDFPage


class _NoLLM:
    def is_available(self) -> bool:
        return False


def test_find_growing_area_pages_by_keywords_without_llm():
    pages = [
        PDFPage(number=1, text="表紙"),
        PDFPage(number=2, text="作付体系\n作物\n面積"),
        PDFPage(number=3, text="収支"),
    ]

    actual = find_growing_area_pages(pages=pages, llm_runtime=_NoLLM())

    assert actual == [2]
