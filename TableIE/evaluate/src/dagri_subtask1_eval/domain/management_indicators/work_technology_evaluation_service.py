from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any

from .work_technologies import WorkTechnologyList


@dataclass(frozen=True)
class WorkTechnologyFieldEvaluation:
    """作業技術一覧の1項目に対する評価結果を表す。"""

    field_name: str
    submission_value: Any
    eval_value: Any
    score: float


class WorkTechnologyEvaluationService(ABC):
    """2つの作業技術一覧を項目ごとに比較評価する契約を定義する。"""

    @abstractmethod
    def evaluate(
        self,
        submission_work_technology: WorkTechnologyList,
        eval_work_technology: WorkTechnologyList,
    ) -> list[WorkTechnologyFieldEvaluation]:
        """作業技術一覧どうしの項目別評価結果を返す。"""
