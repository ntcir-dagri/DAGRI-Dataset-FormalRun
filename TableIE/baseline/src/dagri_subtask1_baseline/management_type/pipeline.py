"""経営類型抽出のオーケストレーション。

概要:
Step1-8の順序で各サブモジュールを呼び出し、`ManagementType`を組み立てます。

実装意図:
処理順序とフォールバック方針（未検出時は初期値維持）を明示し、
実験時の変更点を局所化できるようにします。
"""

from __future__ import annotations

from dagri_subtask1_sdk.domain.management_type import ManagementType

from dagri_subtask1_baseline.management_type.balance.extractor import (
    extract_balance_by_management_type,
)
from dagri_subtask1_baseline.management_type.balance.page_finder import (
    find_balance_pages,
)
from dagri_subtask1_baseline.management_type.capital_equipment.extractor import (
    extract_capital_equipment_by_management_type,
)
from dagri_subtask1_baseline.management_type.capital_equipment.page_finder import (
    find_capital_equipment_pages,
)
from dagri_subtask1_baseline.management_type.growing_area.extractor import (
    extract_growing_area_by_management_type,
)
from dagri_subtask1_baseline.management_type.growing_area.page_finder import (
    find_growing_area_pages,
)
from dagri_subtask1_baseline.management_type.name.extractor import (
    extract_management_type_names,
)
from dagri_subtask1_baseline.management_type.premise.extractor import (
    extract_premise_by_management_type,
)
from dagri_subtask1_baseline.management_type.premise.page_finder import (
    find_premise_pages,
)
from dagri_subtask1_baseline.shared.logging_utils import debug, warn
from dagri_subtask1_baseline.shared.pdf_pages import PDFPage, select_pages


def extract_management_types(
    pages: list[PDFPage],
    llm_runtime,
) -> list[ManagementType]:
    debug(f"management_type pipeline started: pages={len(pages)}")
    management_types = extract_management_type_names(
        pages=pages, llm_runtime=llm_runtime
    )
    debug(f"management_type names extracted: count={len(management_types)}")
    if not management_types:
        return []

    premise_pages = find_premise_pages(pages=pages, llm_runtime=llm_runtime)
    debug(f"premise pages selected: count={len(premise_pages)} pages={premise_pages}")
    if premise_pages:
        premise_values = extract_premise_by_management_type(
            pages=select_pages(pages, premise_pages),
            management_types=management_types,
            llm_runtime=llm_runtime,
        )
        debug(f"premise extracted: count={len(premise_values)}")
        for management_type in management_types:
            if management_type.id in premise_values:
                management_type.premise = premise_values[management_type.id]
    else:
        warn("premise pages were not found. premise keeps default values.")

    growing_area_pages = find_growing_area_pages(pages=pages, llm_runtime=llm_runtime)
    debug(
        f"growing_area pages selected: count={len(growing_area_pages)} pages={growing_area_pages}"
    )
    if growing_area_pages:
        growing_area_values = extract_growing_area_by_management_type(
            pages=select_pages(pages, growing_area_pages),
            management_types=management_types,
            llm_runtime=llm_runtime,
        )
        debug(f"growing_area extracted: count={len(growing_area_values)}")
        for management_type in management_types:
            if management_type.id in growing_area_values:
                management_type.growing_area = growing_area_values[management_type.id]
    else:
        warn("growing_area pages were not found. growing_area keeps default values.")

    balance_pages = find_balance_pages(pages=pages, llm_runtime=llm_runtime)
    debug(f"balance pages selected: count={len(balance_pages)} pages={balance_pages}")
    if balance_pages:
        balance_values = extract_balance_by_management_type(
            pages=select_pages(pages, balance_pages),
            management_types=management_types,
            llm_runtime=llm_runtime,
        )
        debug(f"balance extracted: count={len(balance_values)}")
        for management_type in management_types:
            if management_type.id in balance_values:
                management_type.balance = balance_values[management_type.id]
    else:
        warn("balance pages were not found. balance keeps default values.")

    capital_equipment_pages = find_capital_equipment_pages(
        pages=pages,
        llm_runtime=llm_runtime,
    )
    debug(
        "capital_equipment pages selected: "
        f"count={len(capital_equipment_pages)} pages={capital_equipment_pages}"
    )
    if capital_equipment_pages:
        capital_equipment_values = extract_capital_equipment_by_management_type(
            pages=select_pages(pages, capital_equipment_pages),
            management_types=management_types,
            llm_runtime=llm_runtime,
        )
        debug(f"capital_equipment extracted: count={len(capital_equipment_values)}")
        for management_type in management_types:
            if management_type.id in capital_equipment_values:
                management_type.capital_equipment = capital_equipment_values[
                    management_type.id
                ]
    else:
        warn(
            "capital_equipment pages were not found. capital_equipment keeps default values."
        )

    debug(f"management_type pipeline finished: count={len(management_types)}")
    return management_types
