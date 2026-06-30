from dagri_subtask1_eval.domain.management_indicators.work_technologies import (
    WorkTechnology,
    WorkTechnologyEquipment,
    WorkTechnologyList,
    WorkTechnologyMaterial,
)
from dagri_subtask1_eval.infra.management_indicators.work_technology_evaluation_service import (
    DefaultWorkTechnologyEvaluationService,
)


def test_evaluate_returns_field_level_scores_for_aligned_items() -> None:
    service = DefaultWorkTechnologyEvaluationService()
    submission_work_technology = WorkTechnologyList(
        items=[
            WorkTechnology(
                name="播種",
                description="機械播種",
                eqiupments=[WorkTechnologyEquipment(name="播種機", hour=1.0)],
                materials=[WorkTechnologyMaterial(name="種子", usage="1", usage_unit="kg")],
                number_of_workers=2,
                total_number_of_hours=3.0,
                cost=1000,
                note="共同",
            ),
            WorkTechnology(
                name="収穫",
                description="手作業",
                eqiupments=[],
                materials=[],
                number_of_workers=3,
                total_number_of_hours=5.0,
                cost=2000,
                note=None,
            ),
        ]
    )
    eval_work_technology = WorkTechnologyList(
        items=[
            WorkTechnology(
                name="収穫",
                description="手作業",
                eqiupments=[],
                materials=[],
                number_of_workers=3,
                total_number_of_hours=6.0,
                cost=2000,
                note=None,
            ),
            WorkTechnology(
                name="播種",
                description="機械播種",
                eqiupments=[WorkTechnologyEquipment(name="播種器", hour=1.0)],
                materials=[WorkTechnologyMaterial(name="種子", usage="1", usage_unit="kg")],
                number_of_workers=2,
                total_number_of_hours=3.0,
                cost=1000,
                note="共同",
            ),
        ]
    )

    evaluations = service.evaluate(submission_work_technology, eval_work_technology)
    evaluation_by_name = {evaluation.field_name: evaluation for evaluation in evaluations}

    assert evaluation_by_name["items[0].name"].score == 1.0
    assert evaluation_by_name["items[0].number_of_workers"].score == 1.0
    assert 0.0 < evaluation_by_name["items[0].eqiupments[0].name"].score < 1.0
    assert evaluation_by_name["items[0].materials[0].name"].score == 1.0
    assert evaluation_by_name["items[1].name"].score == 1.0
    assert evaluation_by_name["items[1].total_number_of_hours"].score == 0.0


def test_evaluate_returns_zero_scores_for_unmatched_items() -> None:
    service = DefaultWorkTechnologyEvaluationService()
    submission_work_technology = WorkTechnologyList(
        items=[
            WorkTechnology(
                name="播種",
                description="機械播種",
                eqiupments=[],
                materials=[],
                number_of_workers=2,
                total_number_of_hours=3.0,
                cost=1000,
                note=None,
            )
        ]
    )
    eval_work_technology = WorkTechnologyList(
        items=[
            WorkTechnology(
                name="播種",
                description="機械播種",
                eqiupments=[],
                materials=[],
                number_of_workers=2,
                total_number_of_hours=3.0,
                cost=1000,
                note=None,
            ),
            WorkTechnology(
                name="収穫",
                description="手作業",
                eqiupments=[],
                materials=[],
                number_of_workers=3,
                total_number_of_hours=5.0,
                cost=2000,
                note=None,
            ),
        ]
    )

    evaluations = service.evaluate(submission_work_technology, eval_work_technology)
    evaluation_by_name = {evaluation.field_name: evaluation for evaluation in evaluations}

    assert evaluation_by_name["items[1].name"].score == 0.0
    assert evaluation_by_name["items[1].description"].score == 0.0
    assert evaluation_by_name["items[1].number_of_workers"].score == 0.0
    assert evaluation_by_name["items[1].total_number_of_hours"].score == 0.0
    assert evaluation_by_name["items[1].cost"].score == 0.0


def test_evaluate_treats_float_worker_and_cost_fields_as_match() -> None:
    service = DefaultWorkTechnologyEvaluationService(
        evaluated_item_fields=("number_of_workers", "cost")
    )
    submission_work_technology = WorkTechnologyList(
        items=[WorkTechnology(name="播種", number_of_workers=2.5, cost=1000.25)]
    )
    eval_work_technology = WorkTechnologyList(
        items=[WorkTechnology(name="播種", number_of_workers=2.5, cost=1000.25)]
    )

    evaluations = service.evaluate(submission_work_technology, eval_work_technology)
    evaluation_by_name = {evaluation.field_name: evaluation for evaluation in evaluations}

    assert evaluation_by_name["items[0].number_of_workers"].score == 1.0
    assert evaluation_by_name["items[0].cost"].score == 1.0


def test_evaluate_does_not_align_low_similarity_items() -> None:
    service = DefaultWorkTechnologyEvaluationService(
        min_item_similarity=0.6,
        min_equipment_similarity=0.6,
        min_material_similarity=0.6,
    )
    submission_work_technology = WorkTechnologyList(
        items=[
            WorkTechnology(
                name="播種",
                description="機械播種",
                eqiupments=[WorkTechnologyEquipment(name="播種機", hour=1.0)],
                materials=[WorkTechnologyMaterial(name="種子", usage="1", usage_unit="kg")],
                number_of_workers=2,
                total_number_of_hours=3.0,
                cost=1000,
                note="共同",
            )
        ]
    )
    eval_work_technology = WorkTechnologyList(
        items=[
            WorkTechnology(
                name="収穫",
                description="手作業",
                eqiupments=[WorkTechnologyEquipment(name="収穫機", hour=2.0)],
                materials=[WorkTechnologyMaterial(name="肥料", usage="5", usage_unit="袋")],
                number_of_workers=5,
                total_number_of_hours=8.0,
                cost=4000,
                note="臨時",
            )
        ]
    )

    evaluations = service.evaluate(submission_work_technology, eval_work_technology)
    evaluation_by_name = {evaluation.field_name: evaluation for evaluation in evaluations}

    assert evaluation_by_name["items[0].name"].score == 0.0
    assert evaluation_by_name["items[0].eqiupments[0].name"].score == 0.0
    assert evaluation_by_name["items[0].materials[0].name"].score == 0.0
    assert evaluation_by_name["items[1].name"].score == 0.0
    assert evaluation_by_name["items[1].eqiupments[0].name"].score == 0.0
    assert evaluation_by_name["items[1].materials[0].name"].score == 0.0
