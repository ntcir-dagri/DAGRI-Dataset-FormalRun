from dataclasses import dataclass
from difflib import SequenceMatcher
from typing import Iterable

from dagri_subtask1_eval.domain.management_types.growing_area import (
    GrowingArea,
    GrowingAreaList,
)
from dagri_subtask1_eval.domain.management_types.growing_area_evaluation_service import (
    GrowingAreaEvaluationService,
    GrowingAreaFieldEvaluation,
)


@dataclass(frozen=True)
class _GrowingAreaAlignment:
    submission_growing_area: GrowingArea | None
    eval_growing_area: GrowingArea | None


class DefaultGrowingAreaEvaluationService(GrowingAreaEvaluationService):
    """アプリケーションで利用する栽培面積評価の標準実装ひな形。

    栽培面積は `GrowingArea` の配列として表現されるため、評価ではまず
    提出データ側と正解データ側の各要素を対応付ける必要がある。
    想定する実装方針は次のとおり。

    1. `crop_name` を主な手掛かりとして、必要に応じて `cultivars` も補助的に使い、
       提出側の要素と正解側の要素を1対1に対応付ける。
    2. 対応付けた要素どうしについて、`crop_name`、`cultivars`、`area`、`area_unit`
       を個別に評価する。
    3. 文字列は類似度、数値は完全一致、配列は要素対応付け後の平均スコアという、
       既存の前提表評価と同じ基準を適用する。
    4. 対応付けられなかった要素は未一致として扱い、関連する評価結果を 0 点寄りにする。
    5. 最終的には、利用側が要素単位・項目単位のどちらでも追跡できるような
       評価結果の返し方を目指す。
    """

    DEFAULT_ITEM_FIELDS = ("crop_name", "cultivars", "area", "area_unit")

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
        submission_growing_area: GrowingAreaList,
        eval_growing_area: GrowingAreaList,
    ) -> list[GrowingAreaFieldEvaluation]:
        """上記方針に従って栽培面積情報の比較評価結果を返す。"""
        aligned_items = self._align_items(
            submission_growing_area.items or [], eval_growing_area.items or []
        )
        evaluations: list[GrowingAreaFieldEvaluation] = []

        for index, aligned_item in enumerate(aligned_items):
            for field_name in self._evaluated_item_fields:
                evaluations.append(
                    self._create_field_evaluation(
                        index=index,
                        field_name=field_name,
                        submission_value=None
                        if aligned_item.submission_growing_area is None
                        else getattr(aligned_item.submission_growing_area, field_name),
                        eval_value=None
                        if aligned_item.eval_growing_area is None
                        else getattr(aligned_item.eval_growing_area, field_name),
                    )
                )

        return evaluations

    def _align_items(
        self,
        submission_items: list[GrowingArea],
        eval_items: list[GrowingArea],
    ) -> list[_GrowingAreaAlignment]:
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

        aligned_items: list[_GrowingAreaAlignment] = []
        for submission_index, submission_item in enumerate(submission_items):
            eval_index = aligned_eval_indices_by_submission_index.get(submission_index)
            aligned_items.append(
                _GrowingAreaAlignment(
                    submission_growing_area=submission_item,
                    eval_growing_area=None if eval_index is None else eval_items[eval_index],
                )
            )

        for eval_index, eval_item in enumerate(eval_items):
            if eval_index in used_eval_indices:
                continue
            aligned_items.append(
                _GrowingAreaAlignment(
                    submission_growing_area=None,
                    eval_growing_area=eval_item,
                )
            )

        return aligned_items

    def _create_field_evaluation(
        self,
        index: int,
        field_name: str,
        submission_value: str | int | list[str] | None,
        eval_value: str | int | list[str] | None,
    ) -> GrowingAreaFieldEvaluation:
        return GrowingAreaFieldEvaluation(
            field_name=f"items[{index}].{field_name}",
            submission_value=submission_value,
            eval_value=eval_value,
            score=self._evaluate_value(submission_value, eval_value),
        )

    def _calculate_item_similarity(
        self, submission_item: GrowingArea, eval_item: GrowingArea
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
        submission_value: str | int | list[str] | None,
        eval_value: str | int | list[str] | None,
    ) -> float:
        if submission_value is None and eval_value is None:
            return 1.0
        if submission_value is None or eval_value is None:
            return 0.0
        if isinstance(submission_value, list) and isinstance(eval_value, list):
            return self._evaluate_list(submission_value, eval_value)
        if isinstance(submission_value, str) and isinstance(eval_value, str):
            return self._calculate_string_similarity(submission_value, eval_value)
        if isinstance(submission_value, int) and isinstance(eval_value, int):
            return 1.0 if submission_value == eval_value else 0.0

        return 1.0 if submission_value == eval_value else 0.0

    def _evaluate_list(
        self, submission_values: list[str], eval_values: list[str]
    ) -> float:
        if not submission_values and not eval_values:
            return 1.0
        if not submission_values or not eval_values:
            return 0.0

        candidate_pairs: list[tuple[float, int, int]] = []
        for submission_index, submission_value in enumerate(submission_values):
            for eval_index, eval_value in enumerate(eval_values):
                candidate_pairs.append(
                    (
                        self._calculate_string_similarity(submission_value, eval_value),
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

    @staticmethod
    def _calculate_string_similarity(submission_value: str, eval_value: str) -> float:
        return SequenceMatcher(None, submission_value.strip(), eval_value.strip()).ratio()
