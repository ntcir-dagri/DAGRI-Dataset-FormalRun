from dagri_subtask1_eval.domain.management_type import ManagementType
from dagri_subtask1_eval.domain.management_type_alignment_service import (
    ManagementTypeAlignment,
)
from dagri_subtask1_eval.domain.management_types.balance import Balance
from dagri_subtask1_eval.domain.management_types.capital_equipment import (
    CapitalEquipmentList,
)
from dagri_subtask1_eval.domain.management_types.growing_area import GrowingAreaList
from dagri_subtask1_eval.domain.management_types.premise import Premise
from dagri_subtask1_eval.infra.management_type_alignment_service import (
    SimilarityBasedManagementTypeAlignmentService,
)


def test_align_returns_one_to_one_pairs_when_lengths_are_equal() -> None:
    service = SimilarityBasedManagementTypeAlignmentService()
    submission_management_types = [
        create_management_type("1", "たまねぎ"),
        create_management_type("2", "みかん"),
    ]
    eval_management_types = [
        create_management_type("a", "みかん"),
        create_management_type("b", "たまねぎ"),
    ]

    aligned_pairs = service.align(submission_management_types, eval_management_types)

    assert aligned_pairs == [
        ManagementTypeAlignment(
            submission_management_type=submission_management_types[0],
            eval_management_type=eval_management_types[1],
            similarity=1.0,
        ),
        ManagementTypeAlignment(
            submission_management_type=submission_management_types[1],
            eval_management_type=eval_management_types[0],
            similarity=1.0,
        ),
    ]


def test_align_returns_none_for_unmatched_items_when_lengths_are_different() -> None:
    service = SimilarityBasedManagementTypeAlignmentService()
    submission_management_types = [
        create_management_type("1", "トマト"),
        create_management_type("2", "みかん"),
    ]
    eval_management_types = [
        create_management_type("a", "トマト"),
        create_management_type("b", "いちご"),
        create_management_type("c", "ぶどう"),
    ]

    aligned_pairs = service.align(submission_management_types, eval_management_types)

    assert aligned_pairs == [
        ManagementTypeAlignment(
            submission_management_type=submission_management_types[0],
            eval_management_type=eval_management_types[0],
            similarity=1.0,
        ),
        ManagementTypeAlignment(
            submission_management_type=submission_management_types[1],
            eval_management_type=None,
            similarity=0.0,
        ),
        ManagementTypeAlignment(
            submission_management_type=None,
            eval_management_type=eval_management_types[1],
            similarity=0.0,
        ),
        ManagementTypeAlignment(
            submission_management_type=None,
            eval_management_type=eval_management_types[2],
            similarity=0.0,
        ),
    ]


def test_align_returns_empty_list_for_empty_inputs() -> None:
    service = SimilarityBasedManagementTypeAlignmentService()

    aligned_pairs = service.align([], [])

    assert aligned_pairs == []


def create_management_type(id: str, name: str) -> ManagementType:
    return ManagementType(
        id=id,
        name=name,
        premise=Premise(),
        growing_area=GrowingAreaList(items=[]),
        balance=Balance(),
        capital_equipment=CapitalEquipmentList(items=[]),
    )
