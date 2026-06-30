from dagri_subtask1_baseline.management_type.balance.page_finder import find_balance_pages
from dagri_subtask1_baseline.shared.pdf_pages import PDFPage


class _NoLLM:
    def is_available(self) -> bool:
        return False


def test_find_balance_pages_by_keywords_without_llm():
    pages = [
        PDFPage(number=1, text="表紙"),
        PDFPage(number=2, text="経営収支\n農業総収入\n農業所得"),
        PDFPage(number=3, text="資本装備"),
    ]

    actual = find_balance_pages(pages=pages, llm_runtime=_NoLLM())

    assert actual == [2]
