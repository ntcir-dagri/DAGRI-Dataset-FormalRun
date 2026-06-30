"""作業暦（WorkScheduleList）抽出。

概要:
作業時期と作業時間を抽出し、term_unitも文書表記から決定します。

実装意図:
上中下旬/上下旬の表記差に対応し、提出スキーマ整合を優先します。
"""

from __future__ import annotations

from typing import Literal

import pydantic
from dagri_subtask1_sdk.domain.management_indicators.work_schedule import (
    WorkScheduleList,
)

from dagri_subtask1_baseline.shared.llm_client import build_json_schema_format
from dagri_subtask1_baseline.shared.pdf_pages import PDFPage


class _WorkScheduleItem(pydantic.BaseModel):
    management_indicator_id: str
    work_schedule: WorkScheduleList


class _WorkScheduleExtractionResult(pydantic.BaseModel):
    items: list[_WorkScheduleItem] = pydantic.Field(default_factory=list)


def infer_term_unit_from_pages(pages: list[PDFPage]) -> Literal["上下旬", "上中下旬"]:
    if any("上中下旬" in page.text for page in pages):
        return "上中下旬"
    return "上下旬"


def extract_work_schedule(
    pages: list[PDFPage],
    management_indicators,
    llm_runtime,
) -> dict[str, WorkScheduleList]:
    if not pages:
        return {}

    indicator_list = [
        {"id": item.id, "crop_name": item.crop_name} for item in management_indicators
    ]
    inferred_term_unit = infer_term_unit_from_pages(pages)

    response = llm_runtime.request_json_multimodal(
        system_prompt="Extract crop-specific work schedule entries for each management indicator.",
        page_inputs=_build_page_inputs(pages),
        instructions=(
            "Management indicators:\n"
            f"{indicator_list}\n\n"
            f"Detected term_unit candidate: {inferred_term_unit}\n"
            "Extract work_schedule for each management indicator.\n"
            'Return JSON: {"items": [{"management_indicator_id": str, "work_schedule": {...}}]}\n'
            "Use both page image and OCR text. Prioritize visual table/chart information.\n"
            "If unknown term_unit, use the detected candidate.\n"
            "Do not guess unknown values; set them to null.\n\n"
        ),
        response_model=_WorkScheduleExtractionResult,
        text_format=build_json_schema_format(
            name="_WorkScheduleExtractionResult",
            response_model=_WorkScheduleExtractionResult,
        ),
    )
    parsed = _WorkScheduleExtractionResult.model_validate(response)
    return {item.management_indicator_id: item.work_schedule for item in parsed.items}


def _build_page_inputs(pages: list[PDFPage]) -> list[dict]:
    return [
        {
            "page_number": page.number,
            "text": page.text,
            "image_path": page.image_path,
        }
        for page in pages
    ]
