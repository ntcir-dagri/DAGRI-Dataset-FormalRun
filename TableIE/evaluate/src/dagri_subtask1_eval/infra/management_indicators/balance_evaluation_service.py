from difflib import SequenceMatcher
from typing import Any, Iterable, get_args, get_origin

from dagri_subtask1_eval.domain.management_indicators.balance import Balance
from dagri_subtask1_eval.domain.management_indicators.balance_evaluation_service import (
    BalanceEvaluationService,
    BalanceFieldEvaluation,
)


class DefaultBalanceEvaluationService(BalanceEvaluationService):
    """アプリケーションで利用する経営指標の収支表評価の標準実装ひな形。

    経営指標の収支表は単一の `Balance` オブジェクトとして表現されるため、
    項目ごとに提出値と正解値を直接比較する実装が基本になる。
    想定する実装方針は次のとおり。

    1. 数値項目は完全一致を基本とし、必要に応じて将来は許容誤差を導入できるようにする。
    2. 単位などの文字列項目は文字列類似度で評価する。
    3. 両側が `None` の項目は一致、片側のみ `None` の項目は不一致として扱う。
    4. 利用側が後から集計しやすいよう、評価結果は項目単位で返す。
    """

    DEFAULT_FIELDS = (
        "income",
        "income_unit",
        "gross_revenue",
        "gross_revenue_unit",
        "sales_revenue",
        "sales_revenue_unit",
        "amount_of_yielding_main_product",
        "amount_of_yielding_main_product_unit",
        "unit_price_main_product",
        "unit_price_main_product_unit",
        "other_income",
        "other_income_unit",
        "management_cost_total",
        "management_cost_total_unit",
        "variable_cost_total",
        "variable_cost_total_unit",
        "seedling_cost",
        "seedling_cost_unit",
        "fertilizer_cost",
        "fertilizer_cost_unit",
        "pesticide_cost",
        "pesticide_cost_unit",
        "materials_cost",
        "materials_cost_unit",
        "fuel_and_utilities_cost",
        "fuel_and_utilities_cost_unit",
        "farm_tools_cost",
        "farm_tools_cost_unit",
        "insurance_cost",
        "insurance_cost_unit",
        "packing_freight_fees",
        "packing_freight_fees_unit",
        "fixed_cost_total",
        "fixed_cost_total_unit",
        "machinery_depreciation_cost",
        "machinery_depreciation_cost_unit",
        "machinery_repair_cost",
        "machinery_repair_cost_unit",
        "facility_depreciation_cost",
        "facility_depreciation_cost_unit",
        "facility_repair_cost",
        "facility_repair_cost_unit",
        "labor_cost",
        "labor_cost_unit",
        "land_improvement_and_water_cost",
        "land_improvement_and_water_cost_unit",
        "estimated_amount",
        "estimated_amount_unit",
        "imputed_labor_cost",
        "imputed_labor_cost_unit",
        "imputed_rent_paddy",
        "imputed_rent_paddy_unit",
        "imputed_rent_upland",
        "imputed_rent_upland_unit",
        "imputed_rent_orchard",
        "imputed_rent_orchard_unit",
        "imputed_rent_greenhouse",
        "imputed_rent_greenhouse_unit",
        "imputed_interest_on_capital",
        "imputed_interest_on_capital_unit",
        "production_cost_before_byproduct_deduction",
        "production_cost_before_byproduct_deduction_unit",
    )

    def __init__(self, evaluated_fields: Iterable[str] | None = None) -> None:
        self._evaluated_fields = tuple(
            self.DEFAULT_FIELDS if evaluated_fields is None else evaluated_fields
        )

    def evaluate(
        self, submission_balance: Balance, eval_balance: Balance
    ) -> list[BalanceFieldEvaluation]:
        """上記方針に従って経営指標の収支表の比較評価結果を返す。"""
        evaluations: list[BalanceFieldEvaluation] = []

        for field_name in self._evaluated_fields:
            field_info = Balance.model_fields[field_name]
            submission_value = getattr(submission_balance, field_name)
            eval_value = getattr(eval_balance, field_name)
            evaluations.append(
                BalanceFieldEvaluation(
                    field_name=field_name,
                    submission_value=submission_value,
                    eval_value=eval_value,
                    score=self._evaluate_value(
                        submission_value, eval_value, field_info.annotation
                    ),
                )
            )

        return evaluations

    def _evaluate_value(
        self, submission_value: Any, eval_value: Any, annotation: Any
    ) -> float:
        if submission_value is None and eval_value is None:
            return 1.0
        if submission_value is None or eval_value is None:
            return 0.0

        normalized_annotation = self._unwrap_optional(annotation)
        if self._is_numeric_annotation(normalized_annotation):
            return 1.0 if submission_value == eval_value else 0.0
        if normalized_annotation is str:
            return self._calculate_string_similarity(submission_value, eval_value)

        return 1.0 if submission_value == eval_value else 0.0

    @staticmethod
    def _calculate_string_similarity(submission_value: str, eval_value: str) -> float:
        return SequenceMatcher(None, submission_value.strip(), eval_value.strip()).ratio()

    @staticmethod
    def _unwrap_optional(annotation: Any) -> Any:
        origin = get_origin(annotation)
        if origin is None:
            return annotation

        args = [arg for arg in get_args(annotation) if arg is not type(None)]
        if len(args) == 1:
            return args[0]

        return annotation

    @staticmethod
    def _is_numeric_annotation(annotation: Any) -> bool:
        return annotation in (int, float)
