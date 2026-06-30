"""経営類型名を抽出し、初期ManagementTypeを生成する処理。

概要:
文書全体から類型名候補を抽出し、ID正規化後に初期値入りモデルへ変換します。

実装意図:
後段の項目抽出が失敗しても最小構造を維持できるよう、
ここで必須骨格を先に確定します。
"""

from __future__ import annotations

import pydantic
from dagri_subtask1_sdk.domain.management_type import ManagementType
from dagri_subtask1_sdk.domain.management_types.balance import Balance
from dagri_subtask1_sdk.domain.management_types.capital_equipment import (
    CapitalEquipmentList,
)
from dagri_subtask1_sdk.domain.management_types.growing_area import GrowingAreaList
from dagri_subtask1_sdk.domain.management_types.premise import Premise

from dagri_subtask1_baseline.shared.id_utils import (
    normalize_identifier,
    uniquify_identifiers,
)
from dagri_subtask1_baseline.shared.llm_client import build_json_schema_format
from dagri_subtask1_baseline.shared.pdf_pages import PDFPage


class _NameItem(pydantic.BaseModel):
    id: str | None = None
    name: str


class _NameExtractionResult(pydantic.BaseModel):
    management_types: list[_NameItem] = pydantic.Field(default_factory=list)


def extract_management_type_names(
    pages: list[PDFPage],
    llm_runtime,
) -> list[ManagementType]:
    response = llm_runtime.request_json_multimodal(
        system_prompt=(
            "Extract management type names from Japanese agricultural technical documents."
            " Return only JSON with key management_types."
        ),
        page_inputs=_build_page_inputs(pages),
        instructions=(
            "Extract management type names from the text.\n"
            'Output format: {"management_types": [{"id": str|null, "name": str}]}.\n'
            "Use both page image and OCR text. Prioritize visual table/chart information.\n"
            "If no name found, return empty list.\n\n"
        ),
        response_model=_NameExtractionResult,
        text_format=build_json_schema_format(
            name="_NameExtractionResult", response_model=_NameExtractionResult
        ),
    )
    result = _NameExtractionResult.model_validate(response)

    raw_ids: list[str] = []
    for item in result.management_types:
        id_source = item.id if item.id else item.name
        raw_ids.append(normalize_identifier(id_source))
    unique_ids = uniquify_identifiers(raw_ids)

    management_types: list[ManagementType] = []
    for item, unique_id in zip(result.management_types, unique_ids, strict=True):
        management_types.append(
            ManagementType(
                id=unique_id,
                name=item.name,
                premise=Premise(),
                growing_area=GrowingAreaList(items=None),
                balance=Balance(),
                capital_equipment=CapitalEquipmentList(items=None),
            )
        )

    return management_types


def _build_page_inputs(pages: list[PDFPage]) -> list[dict]:
    return [
        {
            "page_number": page.number,
            "text": page.text,
            "image_path": page.image_path,
        }
        for page in pages
    ]
