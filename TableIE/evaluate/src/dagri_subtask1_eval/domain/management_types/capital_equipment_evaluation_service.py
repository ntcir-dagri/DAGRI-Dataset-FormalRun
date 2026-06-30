from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any

from .capital_equipment import CapitalEquipmentList


@dataclass(frozen=True)
class CapitalEquipmentFieldEvaluation:
    """資本設備・減価償却一覧の1項目に対する評価結果を表す。"""

    field_name: str
    submission_value: Any
    eval_value: Any
    score: float


class CapitalEquipmentEvaluationService(ABC):
    """2つの資本設備・減価償却一覧を項目ごとに比較評価する契約を定義する。"""

    @abstractmethod
    def evaluate(
        self,
        submission_capital_equipment: CapitalEquipmentList,
        eval_capital_equipment: CapitalEquipmentList,
    ) -> list[CapitalEquipmentFieldEvaluation]:
        """資本設備・減価償却一覧どうしの項目別評価結果を返す。"""
