"""前提情報ページ探索。

概要:
キーワード候補とLLM判定を併用して前提表があるページを絞り込みます。

実装意図:
抽出対象ページを狭め、後段のマルチモーダル抽出コストを抑えます。
"""

from __future__ import annotations

import pydantic

from dagri_subtask1_baseline.shared.llm_client import build_json_schema_format, LLMRuntime
from dagri_subtask1_baseline.shared.pdf_pages import PDFPage


class _PageSelection(pydantic.BaseModel):
    page_numbers: list[int] = pydantic.Field(default_factory=list)


_KEYWORDS = ["前提", "該当する地域", "設定した経営規模", "自家労働"]


def find_premise_pages(pages: list[PDFPage], llm_runtime: LLMRuntime) -> list[int]:
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
        system_prompt="Find pages that describe management premise information.",
        user_prompt=(
            "From the candidate pages, select pages that contain premise information.\n"
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
