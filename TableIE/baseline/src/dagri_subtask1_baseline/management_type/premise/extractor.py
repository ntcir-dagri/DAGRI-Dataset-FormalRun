"""前提情報（Premise）抽出。

概要:
対象ページの画像+テキストから、management_typeごとのpremise項目を抽出します。

実装意図:
表形式情報を優先して読むため、マルチモーダル入力を前提にします。
"""

from __future__ import annotations

import pydantic
from dagri_subtask1_sdk.domain.management_types.premise import Premise

from dagri_subtask1_baseline.shared.llm_client import build_json_schema_format
from dagri_subtask1_baseline.shared.pdf_pages import PDFPage


class _PremiseItem(pydantic.BaseModel):
    management_type_id: str
    premise: Premise


class _PremiseExtractionResult(pydantic.BaseModel):
    items: list[_PremiseItem] = pydantic.Field(default_factory=list)


def extract_premise_by_management_type(
    pages: list[PDFPage],
    management_types,
    llm_runtime,
) -> dict[str, Premise]:
    if not pages:
        return {}

    management_type_list = [
        {"id": item.id, "name": item.name} for item in management_types
    ]

    response = llm_runtime.request_json_multimodal(
        system_prompt="Extract premise table values for each management type.",
        page_inputs=_build_page_inputs(pages),
        instructions=(
            "Management types:\n"
            f"{management_type_list}\n\n"
            "Extract premise fields for each management type.\n"
            'Return JSON: {"items": [{"management_type_id": str, "premise": {...}}]}\n'
            "Use both page image and OCR text. Prioritize visual table/chart information.\n"
            "Do not guess unknown values; set them to null.\n\n"
        ),
        response_model=_PremiseExtractionResult,
        text_format=build_json_schema_format(
            name="_PremiseExtractionResult", response_model=_PremiseExtractionResult
        ),
    )
    parsed = _PremiseExtractionResult.model_validate(response)
    return {item.management_type_id: item.premise for item in parsed.items}


def _build_page_inputs(pages: list[PDFPage]) -> list[dict]:
    return [
        {
            "page_number": page.number,
            "text": page.text,
            "image_path": page.image_path,
        }
        for page in pages
    ]
