from difflib import SequenceMatcher
from typing import Any, Iterable, get_args, get_origin

from dagri_subtask1_eval.domain.management_types.balance import Balance
from dagri_subtask1_eval.domain.management_types.balance_evaluation_service import (
    BalanceEvaluationService,
    BalanceFieldEvaluation,
)


class DefaultBalanceEvaluationService(BalanceEvaluationService):
    """アプリケーションで利用する収支表の標準的な項目別評価実装。"""

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
        """収支表の全項目を型ごとのルールに従って評価する。"""
        evaluations: list[BalanceFieldEvaluation] = []

        for field_name in self._evaluated_fields:
            field_info = Balance.model_fields[field_name]
            submission_value = getattr(submission_balance, field_name)
            eval_value = getattr(eval_balance, field_name)
            score = self._evaluate_value(
                submission_value, eval_value, field_info.annotation
            )
            evaluations.append(
                BalanceFieldEvaluation(
                    field_name=field_name,
                    submission_value=submission_value,
                    eval_value=eval_value,
                    score=score,
                )
            )

        return evaluations

    def _evaluate_value(
        self, submission_value: Any, eval_value: Any, annotation: Any
    ) -> float:
        """項目の型に応じて適切な評価ルールへ振り分ける。"""
        if submission_value is None and eval_value is None:
            return 1.0
        if submission_value is None or eval_value is None:
            return 0.0

        normalized_annotation = self._unwrap_optional(annotation)
        if self._is_list_annotation(normalized_annotation):
            return self._evaluate_list(submission_value, eval_value)
        if self._is_numeric_annotation(normalized_annotation):
            return 1.0 if submission_value == eval_value else 0.0
        if normalized_annotation is str:
            return self._calculate_string_similarity(submission_value, eval_value)

        return 1.0 if submission_value == eval_value else 0.0

    def _evaluate_list(self, submission_values: list[Any], eval_values: list[Any]) -> float:
        """配列要素を貪欲に対応付けし、ペアごとのスコア平均を返す。"""
        if not submission_values and not eval_values:
            return 1.0
        if not submission_values or not eval_values:
            return 0.0

        candidate_pairs: list[tuple[float, int, int]] = []
        for submission_index, submission_value in enumerate(submission_values):
            for eval_index, eval_value in enumerate(eval_values):
                candidate_pairs.append(
                    (
                        self._evaluate_list_item(submission_value, eval_value),
                        submission_index,
                        eval_index,
                    )
                )

        candidate_pairs.sort(key=lambda pair: (-pair[0], pair[1], pair[2]))

        matched_submission_indices: set[int] = set()
        matched_eval_indices: set[int] = set()
        scores: list[float] = []

        for score, submission_index, eval_index in candidate_pairs:
            if submission_index in matched_submission_indices:
                continue
            if eval_index in matched_eval_indices:
                continue

            matched_submission_indices.add(submission_index)
            matched_eval_indices.add(eval_index)
            scores.append(score)

        unmatched_count = max(len(submission_values), len(eval_values)) - len(scores)
        scores.extend([0.0] * unmatched_count)

        return sum(scores) / max(len(submission_values), len(eval_values))

    def _evaluate_list_item(self, submission_value: Any, eval_value: Any) -> float:
        """配列内の1要素どうしを基本ルールで評価する。"""
        if submission_value is None and eval_value is None:
            return 1.0
        if submission_value is None or eval_value is None:
            return 0.0
        if isinstance(submission_value, str) and isinstance(eval_value, str):
            return self._calculate_string_similarity(submission_value, eval_value)
        if isinstance(submission_value, (int, float)) and isinstance(eval_value, (int, float)):
            return 1.0 if submission_value == eval_value else 0.0
        return 1.0 if submission_value == eval_value else 0.0

    @staticmethod
    def _calculate_string_similarity(submission_value: str, eval_value: str) -> float:
        """2つの文字列の類似度を0から1の範囲で返す。"""
        return SequenceMatcher(None, submission_value.strip(), eval_value.strip()).ratio()

    @staticmethod
    def _unwrap_optional(annotation: Any) -> Any:
        """Optional型の注釈から、可能なら実体の型を取り出す。"""
        origin = get_origin(annotation)
        if origin is None:
            return annotation

        args = [arg for arg in get_args(annotation) if arg is not type(None)]
        if len(args) == 1:
            return args[0]

        return annotation

    @staticmethod
    def _is_list_annotation(annotation: Any) -> bool:
        """注釈が配列型を表すかどうかを返す。"""
        return get_origin(annotation) is list

    @staticmethod
    def _is_numeric_annotation(annotation: Any) -> bool:
        """注釈が数値型を表すかどうかを返す。"""
        return annotation in (int, float)
