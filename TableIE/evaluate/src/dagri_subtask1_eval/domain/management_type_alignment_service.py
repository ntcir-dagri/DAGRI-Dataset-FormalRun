from dataclasses import dataclass
from abc import ABC, abstractmethod

from .management_type import ManagementType


@dataclass(frozen=True)
class ManagementTypeAlignment:
    submission_management_type: ManagementType | None
    eval_management_type: ManagementType | None
    similarity: float


class ManagementTypeAlignmentService(ABC):
    @abstractmethod
    def align(
        self,
        submission_management_types: list[ManagementType],
        eval_management_types: list[ManagementType],
    ) -> list[ManagementTypeAlignment]:
        """Align submission and evaluation management types."""
