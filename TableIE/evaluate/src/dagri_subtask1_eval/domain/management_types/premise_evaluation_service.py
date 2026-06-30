from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any

from .premise import Premise


@dataclass(frozen=True)
class PremiseFieldEvaluation:
    """前提表の1項目に対する評価結果を表す。"""

    field_name: str
    submission_value: Any
    eval_value: Any
    score: float


class PremiseEvaluationService(ABC):
    """2つの前提表を項目ごとに比較評価する契約を定義する。"""

    @abstractmethod
    def evaluate(
        self, submission_premise: Premise, eval_premise: Premise
    ) -> list[PremiseFieldEvaluation]:
        """前提表どうしの項目別評価結果を返す。"""
