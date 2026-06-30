from dagri_subtask1_eval.domain.management_types.growing_area import (
    GrowingArea,
    GrowingAreaList,
)
from dagri_subtask1_eval.infra.management_types.growing_area_evaluation_service import (
    DefaultGrowingAreaEvaluationService,
)


def test_evaluate_returns_field_level_scores_for_aligned_items() -> None:
    service = DefaultGrowingAreaEvaluationService()
    submission_growing_area = GrowingAreaList(
        items=[
            GrowingArea(
                crop_name="たまねぎ",
                cultivars=["ターザン"],
                area=100,
                area_unit="a",
            ),
            GrowingArea(
                crop_name="みかん",
                cultivars=["青島"],
                area=50,
                area_unit="a",
            ),
        ]
    )
    eval_growing_area = GrowingAreaList(
        items=[
            GrowingArea(
                crop_name="みかん",
                cultivars=["青島"],
                area=60,
                area_unit="a",
            ),
            GrowingArea(
                crop_name="たまねぎ",
                cultivars=["ターサン"],
                area=100,
                area_unit="a",
            ),
        ]
    )

    evaluations = service.evaluate(submission_growing_area, eval_growing_area)
    evaluation_by_name = {evaluation.field_name: evaluation for evaluation in evaluations}

    assert len(evaluations) == 8
    assert evaluation_by_name["items[0].crop_name"].score == 1.0
    assert 0.0 < evaluation_by_name["items[0].cultivars"].score < 1.0
    assert evaluation_by_name["items[0].area"].score == 1.0
    assert evaluation_by_name["items[1].crop_name"].score == 1.0
    assert evaluation_by_name["items[1].area"].score == 0.0


def test_evaluate_returns_zero_scores_for_unmatched_items() -> None:
    service = DefaultGrowingAreaEvaluationService()
    submission_growing_area = GrowingAreaList(
        items=[GrowingArea(crop_name="たまねぎ", cultivars=["ターザン"], area=100, area_unit="a")]
    )
    eval_growing_area = GrowingAreaList(
        items=[
            GrowingArea(crop_name="たまねぎ", cultivars=["ターザン"], area=100, area_unit="a"),
            GrowingArea(crop_name="いちご", cultivars=["ゆめのか"], area=20, area_unit="a"),
        ]
    )

    evaluations = service.evaluate(submission_growing_area, eval_growing_area)
    evaluation_by_name = {evaluation.field_name: evaluation for evaluation in evaluations}

    assert evaluation_by_name["items[1].crop_name"].score == 0.0
    assert evaluation_by_name["items[1].cultivars"].score == 0.0
    assert evaluation_by_name["items[1].area"].score == 0.0
    assert evaluation_by_name["items[1].area_unit"].score == 0.0


def test_evaluate_returns_empty_list_for_empty_inputs() -> None:
    service = DefaultGrowingAreaEvaluationService()

    evaluations = service.evaluate(GrowingAreaList(items=[]), GrowingAreaList(items=[]))

    assert evaluations == []


def test_evaluate_treats_equal_float_area_as_match() -> None:
    service = DefaultGrowingAreaEvaluationService(evaluated_item_fields=("area",))
    submission_growing_area = GrowingAreaList(
        items=[GrowingArea(crop_name="たまねぎ", area=10.5)]
    )
    eval_growing_area = GrowingAreaList(items=[GrowingArea(crop_name="たまねぎ", area=10.5)])

    evaluations = service.evaluate(submission_growing_area, eval_growing_area)

    assert evaluations[0].field_name == "items[0].area"
    assert evaluations[0].score == 1.0


def test_evaluate_does_not_align_low_similarity_items() -> None:
    service = DefaultGrowingAreaEvaluationService(
        evaluated_item_fields=("crop_name", "cultivars", "area", "area_unit"),
        min_similarity=0.6,
    )
    submission_growing_area = GrowingAreaList(
        items=[GrowingArea(crop_name="たまねぎ", cultivars=["ターザン"], area=10, area_unit="a")]
    )
    eval_growing_area = GrowingAreaList(
        items=[GrowingArea(crop_name="りんご", cultivars=["ふじ"], area=20, area_unit="ha")]
    )

    evaluations = service.evaluate(submission_growing_area, eval_growing_area)
    evaluation_by_name = {evaluation.field_name: evaluation for evaluation in evaluations}

    assert evaluation_by_name["items[0].crop_name"].score == 0.0
    assert evaluation_by_name["items[0].cultivars"].score == 0.0
    assert evaluation_by_name["items[0].area"].score == 0.0
    assert evaluation_by_name["items[0].area_unit"].score == 0.0
    assert evaluation_by_name["items[1].crop_name"].score == 0.0
    assert evaluation_by_name["items[1].cultivars"].score == 0.0
    assert evaluation_by_name["items[1].area"].score == 0.0
    assert evaluation_by_name["items[1].area_unit"].score == 0.0
