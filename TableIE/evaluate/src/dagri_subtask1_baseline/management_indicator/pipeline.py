"""経営指標抽出のオーケストレーション。

概要:
growing_area由来の作目を指標化し、balance/work_technologies/work_scheduleを順次反映します。

実装意図:
ページ未検出や抽出失敗時でも初期値維持で継続し、提出生成を止めない設計にします。
"""

from __future__ import annotations

from dagri_subtask1_baseline.management_indicator.balance.extractor import (
    extract_indicator_balance,
)
from dagri_subtask1_baseline.management_indicator.balance.page_finder import (
    find_indicator_balance_pages,
)
from dagri_subtask1_baseline.management_indicator.work_schedule.extractor import (
    extract_work_schedule,
    infer_term_unit_from_pages,
)
from dagri_subtask1_baseline.management_indicator.work_schedule.page_finder import (
    find_work_schedule_pages,
)
from dagri_subtask1_baseline.management_indicator.work_technologies.extractor import (
    extract_work_technologies,
)
from dagri_subtask1_baseline.management_indicator.work_technologies.page_finder import (
    find_work_technologies_pages,
)
from dagri_subtask1_baseline.shared.id_utils import (
    normalize_identifier,
    uniquify_identifiers,
)
from dagri_subtask1_baseline.shared.logging_utils import debug, warn
from dagri_subtask1_baseline.shared.pdf_pages import PDFPage, select_pages
from dagri_subtask1_sdk.domain.management_indicator import ManagementIndicator
from dagri_subtask1_sdk.domain.management_indicators.balance import Balance
from dagri_subtask1_sdk.domain.management_indicators.work_schedule import (
    WorkScheduleList,
)
from dagri_subtask1_sdk.domain.management_indicators.work_technologies import (
    WorkTechnologyList,
)
from dagri_subtask1_sdk.domain.management_type import ManagementType


def extract_management_indicators(
    pages: list[PDFPage],
    management_types: list[ManagementType],
    llm_runtime,
) -> list[ManagementIndicator]:
    debug(
        "management_indicator pipeline started: "
        f"pages={len(pages)} management_types={len(management_types)}"
    )
    crop_names = _collect_crop_names(management_types)
    debug(f"crop names collected: count={len(crop_names)} names={crop_names}")
    if not crop_names:
        return []

    management_indicators = _initialize_management_indicators(
        crop_names=crop_names, pages=pages
    )
    debug(f"management_indicators initialized: count={len(management_indicators)}")

    balance_pages = find_indicator_balance_pages(
        pages=pages,
        llm_runtime=llm_runtime,
        crop_names=crop_names,
    )
    debug(
        f"management_indicator balance pages selected: count={len(balance_pages)} pages={balance_pages}"
    )
    if balance_pages:
        try:
            balance_values = extract_indicator_balance(
                pages=select_pages(pages, balance_pages),
                management_indicators=management_indicators,
                llm_runtime=llm_runtime,
            )
            debug(
                f"management_indicator balance extracted: count={len(balance_values)}"
            )
            for indicator in management_indicators:
                if indicator.id in balance_values:
                    indicator.balance = balance_values[indicator.id]
        except Exception as error:  # noqa: BLE001
            warn(f"failed to extract management_indicator.balance: {error}")
    else:
        warn(
            "management_indicator balance pages were not found. balance keeps default values."
        )

    work_technology_pages = find_work_technologies_pages(
        pages=pages,
        llm_runtime=llm_runtime,
        crop_names=crop_names,
    )
    debug(
        "management_indicator work_technologies pages selected: "
        f"count={len(work_technology_pages)} pages={work_technology_pages}"
    )
    if work_technology_pages:
        try:
            work_technology_values = extract_work_technologies(
                pages=select_pages(pages, work_technology_pages),
                management_indicators=management_indicators,
                llm_runtime=llm_runtime,
            )
            debug(
                f"management_indicator work_technologies extracted: "
                f"count={len(work_technology_values)}"
            )
            for indicator in management_indicators:
                if indicator.id in work_technology_values:
                    indicator.work_technologies = work_technology_values[indicator.id]
        except Exception as error:  # noqa: BLE001
            warn(f"failed to extract management_indicator.work_technologies: {error}")
    else:
        warn(
            "management_indicator work_technologies pages were not found. "
            "work_technologies keeps default values."
        )

    work_schedule_pages = find_work_schedule_pages(
        pages=pages,
        llm_runtime=llm_runtime,
        crop_names=crop_names,
    )
    debug(
        "management_indicator work_schedule pages selected: "
        f"count={len(work_schedule_pages)} pages={work_schedule_pages}"
    )
    if work_schedule_pages:
        try:
            work_schedule_values = extract_work_schedule(
                pages=select_pages(pages, work_schedule_pages),
                management_indicators=management_indicators,
                llm_runtime=llm_runtime,
            )
            debug(
                f"management_indicator work_schedule extracted: count={len(work_schedule_values)}"
            )
            for indicator in management_indicators:
                if indicator.id in work_schedule_values:
                    indicator.work_schedule = work_schedule_values[indicator.id]
        except Exception as error:  # noqa: BLE001
            warn(f"failed to extract management_indicator.work_schedule: {error}")
    else:
        warn(
            "management_indicator work_schedule pages were not found. "
            "work_schedule keeps default values."
        )

    debug(f"management_indicator pipeline finished: count={len(management_indicators)}")
    return management_indicators


def _collect_crop_names(management_types: list[ManagementType]) -> list[str]:
    crop_names: list[str] = []
    seen: set[str] = set()
    for management_type in management_types:
        if management_type.growing_area.items is None:
            continue
        for item in management_type.growing_area.items:
            if item.crop_name is None:
                continue
            name = item.crop_name.strip()
            if not name or name in seen:
                continue
            seen.add(name)
            crop_names.append(name)
    return crop_names


def _initialize_management_indicators(
    crop_names: list[str],
    pages: list[PDFPage],
) -> list[ManagementIndicator]:
    raw_ids = [normalize_identifier(crop_name) for crop_name in crop_names]
    unique_ids = uniquify_identifiers(raw_ids)

    term_unit = infer_term_unit_from_pages(pages)
    return [
        ManagementIndicator(
            id=normalized_id,
            crop_name=crop_name,
            balance=Balance(),
            work_schedule=WorkScheduleList(term_unit=term_unit, items=None),
            work_technologies=WorkTechnologyList(items=None),
        )
        for crop_name, normalized_id in zip(crop_names, unique_ids, strict=True)
    ]
