"""品目別収支ページ探索。

概要:
類型全体収支ではなく作目別収支ページを優先して選別します。

実装意図:
誤って類型全体値を混入させるリスクを下げます。
"""

from __future__ import annotations

import pydantic

from dagri_subtask1_baseline.shared.llm_client import build_json_schema_format
from dagri_subtask1_baseline.shared.pdf_pages import PDFPage


class _PageSelection(pydantic.BaseModel):
    page_numbers: list[int] = pydantic.Field(default_factory=list)


_KEYWORDS = ["収支", "所得", "費用", "作物", "作目", "10a当たり"]


def find_indicator_balance_pages(
    pages: list[PDFPage], llm_runtime, crop_names: list[str]
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
        system_prompt=(
            "Find pages that contain crop-specific management balance data. "
            "Exclude management-type total balance pages."
        ),
        user_prompt=(
            f"Crop names: {crop_names}\n"
            "Select pages that contain crop-specific balance information. "
            "Do not select class-wide total balance pages.\n"
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
