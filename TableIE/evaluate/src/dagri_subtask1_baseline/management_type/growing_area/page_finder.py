"""栽培面積情報ページ探索。"""

from __future__ import annotations

import pydantic

from dagri_subtask1_baseline.shared.llm_client import build_json_schema_format
from dagri_subtask1_baseline.shared.pdf_pages import PDFPage


class _PageSelection(pydantic.BaseModel):
    page_numbers: list[int] = pydantic.Field(default_factory=list)


_KEYWORDS = ["作付", "作物", "栽培", "面積", "技術体系"]


def find_growing_area_pages(pages: list[PDFPage], llm_runtime) -> list[int]:
    candidate_page_numbers = [
        page.number
        for page in pages
        if any(keyword in page.text for keyword in _KEYWORDS)
    ]

    if not llm_runtime.is_available():
        return sorted(set(candidate_page_numbers))

    candidate_text = "\n\n".join(
        f"[page:{page.number}]\n{page.text}"
        for page in pages
        if page.number in candidate_page_numbers
    )
    if not candidate_text:
        return []

    response = llm_runtime.request_json(
        system_prompt="Find pages that describe crops and growing areas.",
        user_prompt=(
            "From the candidate pages, select pages that contain growing area information.\n"
            'Return JSON: {"page_numbers": [int, ...]}\n'
            f"{candidate_text}"
        ),
        response_model=_PageSelection,
        text_format=build_json_schema_format(
            name="_PageSelection", response_model=_PageSelection
        ),
    )
    parsed = _PageSelection.model_validate(response)

    existing = {page.number for page in pages}
    selected = sorted(
        number for number in set(parsed.page_numbers) if number in existing
    )
    if selected:
        return selected
    return sorted(set(candidate_page_numbers))
