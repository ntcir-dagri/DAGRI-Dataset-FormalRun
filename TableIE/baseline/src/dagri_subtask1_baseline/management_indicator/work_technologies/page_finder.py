"""作業技術ページ探索。"""

from __future__ import annotations

import pydantic

from dagri_subtask1_baseline.shared.llm_client import build_json_schema_format
from dagri_subtask1_baseline.shared.pdf_pages import PDFPage


class _PageSelection(pydantic.BaseModel):
    page_numbers: list[int] = pydantic.Field(default_factory=list)


_KEYWORDS = ["技術体系", "作業", "使用資材", "作業体系", "技術項目"]


def find_work_technologies_pages(
    pages: list[PDFPage],
    llm_runtime,
    crop_names: list[str],
) -> list[int]:
    candidate_page_numbers = [
        page.number
        for page in pages
        if any(keyword in page.text for keyword in _KEYWORDS)
        and any(crop_name in page.text for crop_name in crop_names)
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
        system_prompt="Find pages describing crop-specific work technologies.",
        user_prompt=(
            f"Crop names: {crop_names}\n"
            "Select pages that contain work technology details per crop.\n"
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
