"""品目別収支（Balance）抽出。"""

from __future__ import annotations

import pydantic
from dagri_subtask1_sdk.domain.management_indicators.balance import Balance

from dagri_subtask1_baseline.shared.llm_client import build_json_schema_format
from dagri_subtask1_baseline.shared.pdf_pages import PDFPage


class _BalanceItem(pydantic.BaseModel):
    management_indicator_id: str
    balance: Balance


class _BalanceExtractionResult(pydantic.BaseModel):
    items: list[_BalanceItem] = pydantic.Field(default_factory=list)


def extract_indicator_balance(
    pages: list[PDFPage],
    management_indicators,
    llm_runtime,
) -> dict[str, Balance]:
    if not pages:
        return {}

    indicator_list = [
        {"id": item.id, "crop_name": item.crop_name} for item in management_indicators
    ]

    response = llm_runtime.request_json_multimodal(
        system_prompt=(
            "Extract crop-specific balance values for each management indicator. "
            "Exclude class-wide totals."
        ),
        page_inputs=_build_page_inputs(pages),
        instructions=(
            "Management indicators:\n"
            f"{indicator_list}\n\n"
            "Extract balance fields for each management indicator.\n"
            'Return JSON: {"items": [{"management_indicator_id": str, "balance": {...}}]}\n'
            "Use both page image and OCR text. Prioritize visual table/chart information.\n"
            "Do not guess unknown values; set them to null.\n\n"
        ),
        response_model=_BalanceExtractionResult,
        text_format=build_json_schema_format(
            name="_BalanceExtractionResult", response_model=_BalanceExtractionResult
        ),
    )
    parsed = _BalanceExtractionResult.model_validate(response)
    return {item.management_indicator_id: item.balance for item in parsed.items}


def _build_page_inputs(pages: list[PDFPage]) -> list[dict]:
    return [
        {
            "page_number": page.number,
            "text": page.text,
            "image_path": page.image_path,
        }
        for page in pages
    ]
