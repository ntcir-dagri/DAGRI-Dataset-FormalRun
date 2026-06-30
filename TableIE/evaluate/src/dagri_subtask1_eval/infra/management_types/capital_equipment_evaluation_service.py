from dataclasses import dataclass
from difflib import SequenceMatcher
from typing import Iterable

from dagri_subtask1_eval.domain.management_types.capital_equipment import (
    CapitalEquipment,
    CapitalEquipmentList,
)
from dagri_subtask1_eval.domain.management_types.capital_equipment_evaluation_service import (
    CapitalEquipmentEvaluationService,
    CapitalEquipmentFieldEvaluation,
)


@dataclass(frozen=True)
class _CapitalEquipmentAlignment:
    submission_capital_equipment: CapitalEquipment | None
    eval_capital_equipment: CapitalEquipment | None


class DefaultCapitalEquipmentEvaluationService(CapitalEquipmentEvaluationService):
    """アプリケーションで利用する資本設備・減価償却一覧評価の標準実装ひな形。

    資本設備・減価償却一覧は `CapitalEquipment` の配列として表現されるため、
    評価ではまず提出データ側と正解データ側の各要素を対応付ける必要がある。
    想定する実装方針は次のとおり。

    1. `item_name` を主な手掛かりとして、必要に応じて `specification` や `amount`
       も補助的に使い、提出側の要素と正解側の要素を1対1に対応付ける。
    2. 対応付けた要素どうしについて、`item_name`、`amount`、`specification`、
       `acquisition_cost`、`service_life`、`depreciation_cost` を個別に評価する。
    3. 文字列は類似度、数値は完全一致、配列が現れた場合は要素対応付け後の平均
       スコアという、既存の前提表評価と同じ基準を適用する。
    4. 対応付けられなかった要素は未一致として扱い、関連する評価結果を 0 点寄りにする。
    5. 最終的には、利用側が要素単位・項目単位のどちらでも追跡できるような
       評価結果の返し方を目指す。
    """

    DEFAULT_ITEM_FIELDS = (
        "item_name",
        "amount",
        "specification",
        "acquisition_cost",
        "service_life",
        "depreciation_cost",
    )

    def __init__(
        self,
        evaluated_item_fields: Iterable[str] | None = None,
        min_similarity: float = 0.6,
    ) -> None:
        self._evaluated_item_fields = tuple(
            self.DEFAULT_ITEM_FIELDS if evaluated_item_fields is None else evaluated_item_fields
        )
        self._min_similarity = min_similarity

    def evaluate(
        self,
        submission_capital_equipment: CapitalEquipmentList,
        eval_capital_equipment: CapitalEquipmentList,
    ) -> list[CapitalEquipmentFieldEvaluation]:
        """上記方針に従って資本設備・減価償却一覧の比較評価結果を返す。"""
        aligned_items = self._align_items(
            submission_capital_equipment.items or [], eval_capital_equipment.items or []
        )
        evaluations: list[CapitalEquipmentFieldEvaluation] = []

        for index, aligned_item in enumerate(aligned_items):
            for field_name in self._evaluated_item_fields:
                evaluations.append(
                    self._create_field_evaluation(
                        index=index,
                        field_name=field_name,
                        submission_value=None
                        if aligned_item.submission_capital_equipment is None
                        else getattr(aligned_item.submission_capital_equipment, field_name),
                        eval_value=None
                        if aligned_item.eval_capital_equipment is None
                        else getattr(aligned_item.eval_capital_equipment, field_name),
                    )
                )

        return evaluations

    def _align_items(
        self,
        submission_items: list[CapitalEquipment],
        eval_items: list[CapitalEquipment],
    ) -> list[_CapitalEquipmentAlignment]:
        candidate_pairs: list[tuple[float, int, int]] = []
        for submission_index, submission_item in enumerate(submission_items):
            for eval_index, eval_item in enumerate(eval_items):
                similarity = self._calculate_item_similarity(submission_item, eval_item)
                if similarity >= self._min_similarity:
                    candidate_pairs.append((similarity, submission_index, eval_index))

        candidate_pairs.sort(key=lambda pair: (-pair[0], pair[1], pair[2]))

        aligned_eval_indices_by_submission_index: dict[int, int] = {}
        used_eval_indices: set[int] = set()

        for _, submission_index, eval_index in candidate_pairs:
            if submission_index in aligned_eval_indices_by_submission_index:
                continue
            if eval_index in used_eval_indices:
                continue

            aligned_eval_indices_by_submission_index[submission_index] = eval_index
            used_eval_indices.add(eval_index)

        aligned_items: list[_CapitalEquipmentAlignment] = []
        for submission_index, submission_item in enumerate(submission_items):
            eval_index = aligned_eval_indices_by_submission_index.get(submission_index)
            aligned_items.append(
                _CapitalEquipmentAlignment(
                    submission_capital_equipment=submission_item,
                    eval_capital_equipment=None if eval_index is None else eval_items[eval_index],
                )
            )

        for eval_index, eval_item in enumerate(eval_items):
            if eval_index in used_eval_indices:
                continue
            aligned_items.append(
                _CapitalEquipmentAlignment(
                    submission_capital_equipment=None,
                    eval_capital_equipment=eval_item,
                )
            )

        return aligned_items

    def _create_field_evaluation(
        self,
        index: int,
        field_name: str,
        submission_value: str | int | float | None,
        eval_value: str | int | float | None,
    ) -> CapitalEquipmentFieldEvaluation:
        return CapitalEquipmentFieldEvaluation(
            field_name=f"items[{index}].{field_name}",
            submission_value=submission_value,
            eval_value=eval_value,
            score=self._evaluate_value(submission_value, eval_value),
        )

    def _calculate_item_similarity(
        self, submission_item: CapitalEquipment, eval_item: CapitalEquipment
    ) -> float:
        scores = [
            self._evaluate_value(
                getattr(submission_item, field_name), getattr(eval_item, field_name)
            )
            for field_name in self._evaluated_item_fields
        ]
        if not scores:
            return 0.0
        return sum(scores) / len(scores)

    def _evaluate_value(
        self,
        submission_value: str | int | float | None,
        eval_value: str | int | float | None,
    ) -> float:
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
        return SequenceMatcher(None, submission_value.strip(), eval_value.strip()).ratio()
