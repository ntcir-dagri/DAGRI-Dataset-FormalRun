"""作業技術（WorkTechnologyList）抽出。"""

from __future__ import annotations

import pydantic
from dagri_subtask1_sdk.domain.management_indicators.work_technologies import (
    WorkTechnologyList,
)

from dagri_subtask1_baseline.shared.llm_client import build_json_schema_format
from dagri_subtask1_baseline.shared.pdf_pages import PDFPage


class _WorkTechnologiesItem(pydantic.BaseModel):
    management_indicator_id: str
    work_technologies: WorkTechnologyList


class _WorkTechnologiesExtractionResult(pydantic.BaseModel):
    items: list[_WorkTechnologiesItem] = pydantic.Field(default_factory=list)


def extract_work_technologies(
    pages: list[PDFPage],
    management_indicators,
    llm_runtime,
) -> dict[str, WorkTechnologyList]:
    if not pages:
        return {}

    indicator_list = [
        {"id": item.id, "crop_name": item.crop_name} for item in management_indicators
    ]

    response = llm_runtime.request_json_multimodal(
        system_prompt="Extract crop-specific work technology entries for each management indicator.",
        page_inputs=_build_page_inputs(pages),
        instructions=(
            "Management indicators:\n"
            f"{indicator_list}\n\n"
            "Extract work_technologies for each management indicator.\n"
            'Return JSON: {"items": [{"management_indicator_id": str, "work_technologies": {...}}]}\n'
            "Use both page image and OCR text. Prioritize visual table/chart information.\n"
            "Do not guess unknown values; set them to null.\n\n"
        ),
        response_model=_WorkTechnologiesExtractionResult,
        text_format=build_json_schema_format(
            name="_WorkTechnologiesExtractionResult",
            response_model=_WorkTechnologiesExtractionResult,
        ),
    )
    parsed = _WorkTechnologiesExtractionResult.model_validate(response)
    return {
        item.management_indicator_id: item.work_technologies for item in parsed.items
    }


def _build_page_inputs(pages: list[PDFPage]) -> list[dict]:
    return [
        {
            "page_number": page.number,
            "text": page.text,
            "image_path": page.image_path,
        }
        for page in pages
    ]
