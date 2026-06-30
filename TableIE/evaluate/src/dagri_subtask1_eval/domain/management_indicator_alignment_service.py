from dataclasses import dataclass
from abc import ABC, abstractmethod

from .management_indicator import ManagementIndicator


@dataclass(frozen=True)
class ManagementIndicatorAlignment:
    submission_management_indicator: ManagementIndicator | None
    eval_management_indicator: ManagementIndicator | None
    similarity: float


class ManagementIndicatorAlignmentService(ABC):
    @abstractmethod
    def align(
        self,
        submission_management_indicators: list[ManagementIndicator],
        eval_management_indicators: list[ManagementIndicator],
    ) -> list[ManagementIndicatorAlignment]:
        """Align submission and evaluation management indicators."""
