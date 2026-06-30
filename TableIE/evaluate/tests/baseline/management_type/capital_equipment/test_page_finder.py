from dagri_subtask1_baseline.management_type.capital_equipment.page_finder import (
    find_capital_equipment_pages,
)
from dagri_subtask1_baseline.shared.pdf_pages import PDFPage


class _NoLLM:
    def is_available(self) -> bool:
        return False


def test_find_capital_equipment_pages_by_keywords_without_llm():
    pages = [
        PDFPage(number=1, text="表紙"),
        PDFPage(number=2, text="資本装備と減価償却費"),
        PDFPage(number=3, text="収支"),
    ]

    actual = find_capital_equipment_pages(pages=pages, llm_runtime=_NoLLM())

    assert actual == [2]
