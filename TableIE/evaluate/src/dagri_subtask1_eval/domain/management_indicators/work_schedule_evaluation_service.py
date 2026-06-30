from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any

from .work_schedule import WorkScheduleList


@dataclass(frozen=True)
class WorkScheduleFieldEvaluation:
    """作業時間一覧の1項目に対する評価結果を表す。"""

    field_name: str
    submission_value: Any
    eval_value: Any
    score: float


class WorkScheduleEvaluationService(ABC):
    """2つの作業時間一覧を項目ごとに比較評価する契約を定義する。"""

    @abstractmethod
    def evaluate(
        self,
        submission_work_schedule: WorkScheduleList,
        eval_work_schedule: WorkScheduleList,
    ) -> list[WorkScheduleFieldEvaluation]:
        """作業時間一覧どうしの項目別評価結果を返す。"""
