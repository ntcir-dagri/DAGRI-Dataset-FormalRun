from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any

from .growing_area import GrowingAreaList


@dataclass(frozen=True)
class GrowingAreaFieldEvaluation:
    """栽培面積の1項目に対する評価結果を表す。"""

    field_name: str
    submission_value: Any
    eval_value: Any
    score: float


class GrowingAreaEvaluationService(ABC):
    """2つの栽培面積情報を項目ごとに比較評価する契約を定義する。"""

    @abstractmethod
    def evaluate(
        self,
        submission_growing_area: GrowingAreaList,
        eval_growing_area: GrowingAreaList,
    ) -> list[GrowingAreaFieldEvaluation]:
        """栽培面積情報どうしの項目別評価結果を返す。"""
