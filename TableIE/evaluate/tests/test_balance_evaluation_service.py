from dagri_subtask1_eval.domain.management_types.balance import Balance
from dagri_subtask1_eval.infra.management_types.balance_evaluation_service import (
    DefaultBalanceEvaluationService,
)


def test_evaluate_returns_field_level_scores() -> None:
    """複数の収支表項目が、それぞれ想定どおりのルールで評価されることを確認する。"""
    service = DefaultBalanceEvaluationService()
    submission_balance = Balance(
        income=1000.0,
        income_unit="円",
        gross_revenue=2000.0,
        gross_revenue_unit="千円",
        sales_revenue=None,
        sales_revenue_unit="円",
    )
    eval_balance = Balance(
        income=1000.0,
        income_unit="円",
        gross_revenue=1500.0,
        gross_revenue_unit="円",
        sales_revenue=None,
        sales_revenue_unit=None,
    )

    evaluations = service.evaluate(submission_balance, eval_balance)

    evaluation_by_name = {evaluation.field_name: evaluation for evaluation in evaluations}

    assert len(evaluations) == len(Balance.model_fields)
    assert evaluation_by_name["income"].score == 1.0
    assert evaluation_by_name["income_unit"].score == 1.0
    assert evaluation_by_name["gross_revenue"].score == 0.0
    assert 0.0 < evaluation_by_name["gross_revenue_unit"].score < 1.0
    assert evaluation_by_name["sales_revenue"].score == 1.0
    assert evaluation_by_name["sales_revenue_unit"].score == 0.0


def test_evaluate_returns_zero_when_only_one_side_is_none() -> None:
    """片側だけがNoneの任意の数値項目は0点になることを確認する。"""
    service = DefaultBalanceEvaluationService()
    submission_balance = Balance(other_income=None)
    eval_balance = Balance(other_income=100.0)

    evaluations = service.evaluate(submission_balance, eval_balance)
    evaluation_by_name = {evaluation.field_name: evaluation for evaluation in evaluations}

    assert evaluation_by_name["other_income"].score == 0.0
