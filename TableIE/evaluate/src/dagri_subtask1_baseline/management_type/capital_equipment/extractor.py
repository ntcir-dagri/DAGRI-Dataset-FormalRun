"""資本設備（CapitalEquipmentList）抽出。"""

from __future__ import annotations

import pydantic
from dagri_subtask1_sdk.domain.management_types.capital_equipment import (
    CapitalEquipmentList,
)

from dagri_subtask1_baseline.shared.llm_client import build_json_schema_format
from dagri_subtask1_baseline.shared.pdf_pages import PDFPage


class _CapitalEquipmentItem(pydantic.BaseModel):
    management_type_id: str
    capital_equipment: CapitalEquipmentList


class _CapitalEquipmentExtractionResult(pydantic.BaseModel):
    items: list[_CapitalEquipmentItem] = pydantic.Field(default_factory=list)


def extract_capital_equipment_by_management_type(
    pages: list[PDFPage],
    management_types,
    llm_runtime,
) -> dict[str, CapitalEquipmentList]:
    if not pages:
        return {}

    management_type_list = [
        {"id": item.id, "name": item.name} for item in management_types
    ]

    response = llm_runtime.request_json_multimodal(
        system_prompt="Extract capital equipment rows for each management type.",
        page_inputs=_build_page_inputs(pages),
        instructions=(
            "Management types:\n"
            f"{management_type_list}\n\n"
            "Extract capital equipment fields for each management type.\n"
            'Return JSON: {"items": [{"management_type_id": str, "capital_equipment": {...}}]}\n'
            "amount can be integer or decimal (e.g. 1 or 1.5).\n"
            "Use both page image and OCR text. Prioritize visual table/chart information.\n"
            "Do not guess unknown values; set them to null.\n\n"
        ),
        response_model=_CapitalEquipmentExtractionResult,
        text_format=build_json_schema_format(
            name="_CapitalEquipmentExtractionResult",
            response_model=_CapitalEquipmentExtractionResult,
        ),
    )
    parsed = _CapitalEquipmentExtractionResult.model_validate(response)
    return {item.management_type_id: item.capital_equipment for item in parsed.items}


def _build_page_inputs(pages: list[PDFPage]) -> list[dict]:
    return [
        {
            "page_number": page.number,
            "text": page.text,
            "image_path": page.image_path,
        }
        for page in pages
    ]
