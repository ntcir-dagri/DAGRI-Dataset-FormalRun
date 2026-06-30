from dagri_subtask1_eval.domain.management_indicator import ManagementIndicator
from dagri_subtask1_eval.domain.management_indicator_alignment_service import (
    ManagementIndicatorAlignment,
)
from dagri_subtask1_eval.domain.management_indicators.balance import Balance
from dagri_subtask1_eval.domain.management_indicators.work_schedule import (
    WorkScheduleList,
)
from dagri_subtask1_eval.domain.management_indicators.work_technologies import (
    WorkTechnologyList,
)
from dagri_subtask1_eval.infra.management_indicator_alignment_service import (
    SimilarityBasedManagementIndicatorAlignmentService,
)


def test_align_returns_one_to_one_pairs_when_lengths_are_equal() -> None:
    service = SimilarityBasedManagementIndicatorAlignmentService()
    submission_management_indicators = [
        create_management_indicator("1", "たまねぎ"),
        create_management_indicator("2", "みかん"),
    ]
    eval_management_indicators = [
        create_management_indicator("a", "みかん"),
        create_management_indicator("b", "たまねぎ"),
    ]

    aligned_pairs = service.align(
        submission_management_indicators, eval_management_indicators
    )

    assert aligned_pairs == [
        ManagementIndicatorAlignment(
            submission_management_indicator=submission_management_indicators[0],
            eval_management_indicator=eval_management_indicators[1],
            similarity=1.0,
        ),
        ManagementIndicatorAlignment(
            submission_management_indicator=submission_management_indicators[1],
            eval_management_indicator=eval_management_indicators[0],
            similarity=1.0,
        ),
    ]


def test_align_returns_none_for_unmatched_items_when_lengths_are_different() -> None:
    service = SimilarityBasedManagementIndicatorAlignmentService()
    submission_management_indicators = [
        create_management_indicator("1", "トマト"),
        create_management_indicator("2", "みかん"),
    ]
    eval_management_indicators = [
        create_management_indicator("a", "トマト"),
        create_management_indicator("b", "いちご"),
        create_management_indicator("c", "ぶどう"),
    ]

    aligned_pairs = service.align(
        submission_management_indicators, eval_management_indicators
    )

    assert aligned_pairs == [
        ManagementIndicatorAlignment(
            submission_management_indicator=submission_management_indicators[0],
            eval_management_indicator=eval_management_indicators[0],
            similarity=1.0,
        ),
        ManagementIndicatorAlignment(
            submission_management_indicator=submission_management_indicators[1],
            eval_management_indicator=None,
            similarity=0.0,
        ),
        ManagementIndicatorAlignment(
            submission_management_indicator=None,
            eval_management_indicator=eval_management_indicators[1],
            similarity=0.0,
        ),
        ManagementIndicatorAlignment(
            submission_management_indicator=None,
            eval_management_indicator=eval_management_indicators[2],
            similarity=0.0,
        ),
    ]


def test_align_returns_empty_list_for_empty_inputs() -> None:
    service = SimilarityBasedManagementIndicatorAlignmentService()

    aligned_pairs = service.align([], [])

    assert aligned_pairs == []


def create_management_indicator(id: str, crop_name: str) -> ManagementIndicator:
    return ManagementIndicator(
        id=id,
        crop_name=crop_name,
        balance=Balance(),
        work_schedule=WorkScheduleList(term_unit="上中下旬", items=[]),
        work_technologies=WorkTechnologyList(items=[]),
    )
