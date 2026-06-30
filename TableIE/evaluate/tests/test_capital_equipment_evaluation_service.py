from dagri_subtask1_eval.domain.management_types.capital_equipment import (
    CapitalEquipment,
    CapitalEquipmentList,
)
from dagri_subtask1_eval.infra.management_types.capital_equipment_evaluation_service import (
    DefaultCapitalEquipmentEvaluationService,
)


def test_evaluate_returns_field_level_scores_for_aligned_items() -> None:
    service = DefaultCapitalEquipmentEvaluationService()
    submission_capital_equipment = CapitalEquipmentList(
        items=[
            CapitalEquipment(
                item_name="トラクター",
                amount=1,
                specification="20PS",
                acquisition_cost=1000000,
                service_life=7,
                depreciation_cost=100000,
            ),
            CapitalEquipment(
                item_name="管理機",
                amount=1,
                specification="6PS",
                acquisition_cost=300000,
                service_life=7,
                depreciation_cost=30000,
            ),
        ]
    )
    eval_capital_equipment = CapitalEquipmentList(
        items=[
            CapitalEquipment(
                item_name="管理機",
                amount=1,
                specification="6PS",
                acquisition_cost=350000,
                service_life=7,
                depreciation_cost=30000,
            ),
            CapitalEquipment(
                item_name="トラクター",
                amount=1,
                specification="20馬力",
                acquisition_cost=1000000,
                service_life=7,
                depreciation_cost=100000,
            ),
        ]
    )

    evaluations = service.evaluate(submission_capital_equipment, eval_capital_equipment)
    evaluation_by_name = {evaluation.field_name: evaluation for evaluation in evaluations}

    assert len(evaluations) == 12
    assert evaluation_by_name["items[0].item_name"].score == 1.0
    assert 0.0 < evaluation_by_name["items[0].specification"].score < 1.0
    assert evaluation_by_name["items[0].acquisition_cost"].score == 1.0
    assert evaluation_by_name["items[1].item_name"].score == 1.0
    assert evaluation_by_name["items[1].acquisition_cost"].score == 0.0


def test_evaluate_returns_zero_scores_for_unmatched_items() -> None:
    service = DefaultCapitalEquipmentEvaluationService()
    submission_capital_equipment = CapitalEquipmentList(
        items=[
            CapitalEquipment(
                item_name="トラクター",
                amount=1,
                specification="20PS",
                acquisition_cost=1000000,
                service_life=7,
                depreciation_cost=100000,
            )
        ]
    )
    eval_capital_equipment = CapitalEquipmentList(
        items=[
            CapitalEquipment(
                item_name="トラクター",
                amount=1,
                specification="20PS",
                acquisition_cost=1000000,
                service_life=7,
                depreciation_cost=100000,
            ),
            CapitalEquipment(
                item_name="乾燥機",
                amount=1,
                specification="大型",
                acquisition_cost=500000,
                service_life=10,
                depreciation_cost=50000,
            ),
        ]
    )

    evaluations = service.evaluate(submission_capital_equipment, eval_capital_equipment)
    evaluation_by_name = {evaluation.field_name: evaluation for evaluation in evaluations}

    assert evaluation_by_name["items[1].item_name"].score == 0.0
    assert evaluation_by_name["items[1].amount"].score == 0.0
    assert evaluation_by_name["items[1].specification"].score == 0.0
    assert evaluation_by_name["items[1].acquisition_cost"].score == 0.0
    assert evaluation_by_name["items[1].service_life"].score == 0.0
    assert evaluation_by_name["items[1].depreciation_cost"].score == 0.0


def test_evaluate_returns_empty_list_for_empty_inputs() -> None:
    service = DefaultCapitalEquipmentEvaluationService()

    evaluations = service.evaluate(CapitalEquipmentList(items=[]), CapitalEquipmentList(items=[]))

    assert evaluations == []


def test_evaluate_treats_equal_float_amount_as_match() -> None:
    service = DefaultCapitalEquipmentEvaluationService(evaluated_item_fields=("amount",))
    submission_capital_equipment = CapitalEquipmentList(
        items=[CapitalEquipment(item_name="散布機", amount=1.5)]
    )
    eval_capital_equipment = CapitalEquipmentList(
        items=[CapitalEquipment(item_name="散布機", amount=1.5)]
    )

    evaluations = service.evaluate(submission_capital_equipment, eval_capital_equipment)

    assert evaluations[0].field_name == "items[0].amount"
    assert evaluations[0].score == 1.0


def test_evaluate_treats_different_float_amount_as_mismatch() -> None:
    service = DefaultCapitalEquipmentEvaluationService(evaluated_item_fields=("amount",))
    submission_capital_equipment = CapitalEquipmentList(
        items=[CapitalEquipment(item_name="散布機", amount=1.5)]
    )
    eval_capital_equipment = CapitalEquipmentList(
        items=[CapitalEquipment(item_name="散布機", amount=1.6)]
    )

    evaluations = service.evaluate(submission_capital_equipment, eval_capital_equipment)

    assert evaluations[0].field_name == "items[0].amount"
    assert evaluations[0].score == 0.0


def test_evaluate_treats_int_and_float_amount_as_equal() -> None:
    service = DefaultCapitalEquipmentEvaluationService(evaluated_item_fields=("amount",))
    submission_capital_equipment = CapitalEquipmentList(
        items=[CapitalEquipment(item_name="散布機", amount=1)]
    )
    eval_capital_equipment = CapitalEquipmentList(
        items=[CapitalEquipment(item_name="散布機", amount=1.0)]
    )

    evaluations = service.evaluate(submission_capital_equipment, eval_capital_equipment)

    assert evaluations[0].field_name == "items[0].amount"
    assert evaluations[0].score == 1.0


def test_evaluate_treats_float_cost_fields_as_match() -> None:
    service = DefaultCapitalEquipmentEvaluationService(
        evaluated_item_fields=("acquisition_cost", "service_life", "depreciation_cost")
    )
    submission_capital_equipment = CapitalEquipmentList(
        items=[
            CapitalEquipment(
                item_name="散布機",
                acquisition_cost=1000000.5,
                service_life=7.5,
                depreciation_cost=100000.25,
            )
        ]
    )
    eval_capital_equipment = CapitalEquipmentList(
        items=[
            CapitalEquipment(
                item_name="散布機",
                acquisition_cost=1000000.5,
                service_life=7.5,
                depreciation_cost=100000.25,
            )
        ]
    )

    evaluations = service.evaluate(submission_capital_equipment, eval_capital_equipment)
    evaluation_by_name = {evaluation.field_name: evaluation for evaluation in evaluations}

    assert evaluation_by_name["items[0].acquisition_cost"].score == 1.0
    assert evaluation_by_name["items[0].service_life"].score == 1.0
    assert evaluation_by_name["items[0].depreciation_cost"].score == 1.0


def test_evaluate_does_not_align_low_similarity_items() -> None:
    service = DefaultCapitalEquipmentEvaluationService(
        evaluated_item_fields=(
            "item_name",
            "amount",
            "specification",
            "acquisition_cost",
            "service_life",
            "depreciation_cost",
        ),
        min_similarity=0.6,
    )
    submission_capital_equipment = CapitalEquipmentList(
        items=[
            CapitalEquipment(
                item_name="トラクター",
                amount=1,
                specification="20PS",
                acquisition_cost=1000000,
                service_life=7,
                depreciation_cost=100000,
            )
        ]
    )
    eval_capital_equipment = CapitalEquipmentList(
        items=[
            CapitalEquipment(
                item_name="乾燥機",
                amount=2,
                specification="大型",
                acquisition_cost=500000,
                service_life=10,
                depreciation_cost=50000,
            )
        ]
    )

    evaluations = service.evaluate(submission_capital_equipment, eval_capital_equipment)
    evaluation_by_name = {evaluation.field_name: evaluation for evaluation in evaluations}

    assert evaluation_by_name["items[0].item_name"].score == 0.0
    assert evaluation_by_name["items[0].amount"].score == 0.0
    assert evaluation_by_name["items[0].specification"].score == 0.0
    assert evaluation_by_name["items[0].acquisition_cost"].score == 0.0
    assert evaluation_by_name["items[0].service_life"].score == 0.0
    assert evaluation_by_name["items[0].depreciation_cost"].score == 0.0
    assert evaluation_by_name["items[1].item_name"].score == 0.0
    assert evaluation_by_name["items[1].amount"].score == 0.0
    assert evaluation_by_name["items[1].specification"].score == 0.0
    assert evaluation_by_name["items[1].acquisition_cost"].score == 0.0
    assert evaluation_by_name["items[1].service_life"].score == 0.0
    assert evaluation_by_name["items[1].depreciation_cost"].score == 0.0
