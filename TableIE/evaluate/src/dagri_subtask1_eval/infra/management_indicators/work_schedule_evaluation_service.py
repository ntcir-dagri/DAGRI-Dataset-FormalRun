from dataclasses import dataclass
from difflib import SequenceMatcher
from typing import Iterable

from dagri_subtask1_eval.domain.management_indicators.work_schedule import WorkSchedule
from dagri_subtask1_eval.domain.management_indicators.work_schedule import WorkScheduleList
from dagri_subtask1_eval.domain.management_indicators.work_schedule_evaluation_service import (
    WorkScheduleEvaluationService,
    WorkScheduleFieldEvaluation,
)


@dataclass(frozen=True)
class _WorkScheduleAlignment:
    submission_work_schedule: WorkSchedule | None
    eval_work_schedule: WorkSchedule | None


class DefaultWorkScheduleEvaluationService(WorkScheduleEvaluationService):
    """アプリケーションで利用する作業時間一覧評価の標準実装ひな形。

    作業時間一覧は `WorkSchedule` の配列として表現されるため、
    評価ではまず提出データ側と正解データ側の各要素を対応付ける必要がある。
    想定する実装方針は次のとおり。

    1. `name` と `period` を主な手掛かりとして、必要に応じて `hours` も補助的に使い、
       提出側の要素と正解側の要素を1対1に対応付ける。
    2. 対応付けた要素どうしについて、`name`、`period`、`hours` を個別に評価する。
    3. 文字列や列挙値は類似度または一致判定、数値は完全一致を基本とする。
    4. 対応付けられなかった要素は未一致として扱い、関連する評価結果を 0 点寄りにする。
    5. 利用側が要素単位・項目単位の両方で追跡できるような返し方を目指す。
    """

    DEFAULT_ITEM_FIELDS = ("name", "period", "hours")

    def __init__(
        self,
        evaluated_fields: Iterable[str] | None = None,
        evaluated_item_fields: Iterable[str] | None = None,
        min_similarity: float = 0.6,
    ) -> None:
        self._evaluated_fields = tuple(
            ("term_unit",) if evaluated_fields is None else evaluated_fields
        )
        self._evaluated_item_fields = tuple(
            self.DEFAULT_ITEM_FIELDS if evaluated_item_fields is None else evaluated_item_fields
        )
        self._min_similarity = min_similarity

    def evaluate(
        self,
        submission_work_schedule: WorkScheduleList,
        eval_work_schedule: WorkScheduleList,
    ) -> list[WorkScheduleFieldEvaluation]:
        """上記方針に従って作業時間一覧の比較評価結果を返す。"""
        evaluations = []
        for field_name in self._evaluated_fields:
            evaluations.append(
                WorkScheduleFieldEvaluation(
                    field_name=field_name,
                    submission_value=getattr(submission_work_schedule, field_name),
                    eval_value=getattr(eval_work_schedule, field_name),
                    score=self._evaluate_string(
                        getattr(submission_work_schedule, field_name),
                        getattr(eval_work_schedule, field_name),
                    ),
                )
            )

        aligned_items = self._align_items(
            submission_work_schedule.items or [], eval_work_schedule.items or []
        )
        for index, aligned_item in enumerate(aligned_items):
            for field_name in self._evaluated_item_fields:
                evaluations.append(
                    self._create_field_evaluation(
                        index=index,
                        field_name=field_name,
                        submission_value=None
                        if aligned_item.submission_work_schedule is None
                        else getattr(aligned_item.submission_work_schedule, field_name),
                        eval_value=None
                        if aligned_item.eval_work_schedule is None
                        else getattr(aligned_item.eval_work_schedule, field_name),
                    )
                )

        return evaluations

    def _align_items(
        self,
        submission_items: list[WorkSchedule],
        eval_items: list[WorkSchedule],
    ) -> list[_WorkScheduleAlignment]:
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

        aligned_items: list[_WorkScheduleAlignment] = []
        for submission_index, submission_item in enumerate(submission_items):
            eval_index = aligned_eval_indices_by_submission_index.get(submission_index)
            aligned_items.append(
                _WorkScheduleAlignment(
                    submission_work_schedule=submission_item,
                    eval_work_schedule=None if eval_index is None else eval_items[eval_index],
                )
            )

        for eval_index, eval_item in enumerate(eval_items):
            if eval_index in used_eval_indices:
                continue
            aligned_items.append(
                _WorkScheduleAlignment(
                    submission_work_schedule=None,
                    eval_work_schedule=eval_item,
                )
            )

        return aligned_items

    def _calculate_item_similarity(
        self, submission_item: WorkSchedule, eval_item: WorkSchedule
    ) -> float:
        scores = [
            self._evaluate_field(
                field_name,
                getattr(submission_item, field_name),
                getattr(eval_item, field_name),
            )
            for field_name in self._evaluated_item_fields
        ]
        if not scores:
            return 0.0
        return sum(scores) / len(scores)

    def _create_field_evaluation(
        self,
        index: int,
        field_name: str,
        submission_value: object,
        eval_value: object,
    ) -> WorkScheduleFieldEvaluation:
        return WorkScheduleFieldEvaluation(
            field_name=f"items[{index}].{field_name}",
            submission_value=submission_value,
            eval_value=eval_value,
            score=self._evaluate_field(field_name, submission_value, eval_value),
        )

    def _evaluate_field(
        self, field_name: str, submission_value: object, eval_value: object
    ) -> float:
        if field_name == "name":
            return self._evaluate_string(submission_value, eval_value)
        if field_name == "period":
            return self._evaluate_period(submission_value, eval_value)
        return self._evaluate_numeric(submission_value, eval_value)

    @staticmethod
    def _evaluate_string(submission_value: object, eval_value: object) -> float:
        if submission_value is None and eval_value is None:
            return 1.0
        if submission_value is None or eval_value is None:
            return 0.0
        return SequenceMatcher(
            None, str(submission_value).strip(), str(eval_value).strip()
        ).ratio()

    @staticmethod
    def _evaluate_period(submission_value: object, eval_value: object) -> float:
        if submission_value is None and eval_value is None:
            return 1.0
        if submission_value is None or eval_value is None:
            return 0.0
        return 1.0 if submission_value == eval_value else 0.0

    @staticmethod
    def _evaluate_numeric(submission_value: object, eval_value: object) -> float:
        if submission_value is None and eval_value is None:
            return 1.0
        if submission_value is None or eval_value is None:
            return 0.0
        return 1.0 if submission_value == eval_value else 0.0
