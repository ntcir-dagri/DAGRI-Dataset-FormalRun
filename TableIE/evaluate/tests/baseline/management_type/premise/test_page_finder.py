from dagri_subtask1_baseline.management_type.premise.page_finder import find_premise_pages
from dagri_subtask1_baseline.shared.pdf_pages import PDFPage


class _NoLLM:
    def is_available(self) -> bool:
        return False


def test_find_premise_pages_by_keywords_without_llm():
    pages = [
        PDFPage(number=1, text="表紙"),
        PDFPage(number=2, text="1 前提\n該当する地域\n設定した経営規模"),
        PDFPage(number=3, text="収支"),
    ]

    actual = find_premise_pages(pages=pages, llm_runtime=_NoLLM())

    assert actual == [2]
