from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any

from .balance import Balance


@dataclass(frozen=True)
class BalanceFieldEvaluation:
    """経営指標の収支表の1項目に対する評価結果を表す。"""

    field_name: str
    submission_value: Any
    eval_value: Any
    score: float


class BalanceEvaluationService(ABC):
    """2つの経営指標の収支表を項目ごとに比較評価する契約を定義する。"""

    @abstractmethod
    def evaluate(
        self, submission_balance: Balance, eval_balance: Balance
    ) -> list[BalanceFieldEvaluation]:
        """経営指標の収支表どうしの項目別評価結果を返す。"""
