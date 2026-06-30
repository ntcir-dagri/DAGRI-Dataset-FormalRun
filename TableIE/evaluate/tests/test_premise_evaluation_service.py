from dagri_subtask1_eval.domain.management_types.premise import Premise
from dagri_subtask1_eval.infra.management_types.premise_evaluation_service import (
    DefaultPremiseEvaluationService,
)


def test_evaluate_returns_field_level_scores() -> None:
    """複数の型の項目が、それぞれ想定どおりのルールで評価されることを確認する。"""
    service = DefaultPremiseEvaluationService()
    submission_premise = Premise(
        prefecture_name="nagasaki",
        area_name="shimabara",
        crop_names=["たまねぎ", "みかん"],
        cultivate_land=100,
        cultivate_land_unit="a",
        borrowed_cultivate_land=None,
        owned_cultivate_land=80,
        labor_raw="2人",
        labors=2.0,
        total_income=1000,
        total_labor_hours=120.0,
        note="共同利用あり",
    )
    eval_premise = Premise(
        prefecture_name="nagasaki",
        area_name="simabara",
        crop_names=["たまねぎ", "りんご"],
        cultivate_land=100,
        cultivate_land_unit="a",
        borrowed_cultivate_land=None,
        owned_cultivate_land=60,
        labor_raw="2 名",
        labors=2.5,
        total_income=1000,
        total_labor_hours=120.0,
        note="共同利用あり",
    )

    evaluations = service.evaluate(submission_premise, eval_premise)

    evaluation_by_name = {evaluation.field_name: evaluation for evaluation in evaluations}

    assert len(evaluations) == len(Premise.model_fields)
    assert evaluation_by_name["prefecture_name"].score == 1.0
    assert 0.0 < evaluation_by_name["area_name"].score < 1.0
    assert 0.5 < evaluation_by_name["crop_names"].score < 1.0
    assert evaluation_by_name["cultivate_land"].score == 1.0
    assert evaluation_by_name["borrowed_cultivate_land"].score == 1.0
    assert evaluation_by_name["owned_cultivate_land"].score == 0.0
    assert 0.0 < evaluation_by_name["labor_raw"].score < 1.0
    assert evaluation_by_name["labors"].score == 0.0
    assert evaluation_by_name["total_income"].score == 1.0
    assert evaluation_by_name["total_labor_hours"].score == 1.0
    assert evaluation_by_name["note"].score == 1.0


def test_evaluate_returns_zero_when_only_one_side_is_none() -> None:
    """片側だけがNoneの任意項目は0点になることを確認する。"""
    service = DefaultPremiseEvaluationService()
    submission_premise = Premise(note=None)
    eval_premise = Premise(note="あり")

    evaluations = service.evaluate(submission_premise, eval_premise)
    evaluation_by_name = {evaluation.field_name: evaluation for evaluation in evaluations}

    assert evaluation_by_name["note"].score == 0.0


def test_evaluate_returns_one_for_both_empty_lists() -> None:
    """両側が空配列の項目は完全一致として扱われることを確認する。"""
    service = DefaultPremiseEvaluationService()
    submission_premise = Premise(crop_names=[])
    eval_premise = Premise(crop_names=[])

    evaluations = service.evaluate(submission_premise, eval_premise)
    evaluation_by_name = {evaluation.field_name: evaluation for evaluation in evaluations}

    assert evaluation_by_name["crop_names"].score == 1.0


def test_evaluate_treats_float_numeric_fields_as_match() -> None:
    service = DefaultPremiseEvaluationService(
        evaluated_fields=(
            "cultivate_land",
            "borrowed_cultivate_land",
            "owned_cultivate_land",
            "total_income",
        )
    )
    submission_premise = Premise(
        cultivate_land=100.5,
        borrowed_cultivate_land=20.25,
        owned_cultivate_land=80.25,
        total_income=1000.75,
    )
    eval_premise = Premise(
        cultivate_land=100.5,
        borrowed_cultivate_land=20.25,
        owned_cultivate_land=80.25,
        total_income=1000.75,
    )

    evaluations = service.evaluate(submission_premise, eval_premise)
    evaluation_by_name = {evaluation.field_name: evaluation for evaluation in evaluations}

    assert evaluation_by_name["cultivate_land"].score == 1.0
    assert evaluation_by_name["borrowed_cultivate_land"].score == 1.0
    assert evaluation_by_name["owned_cultivate_land"].score == 1.0
    assert evaluation_by_name["total_income"].score == 1.0
