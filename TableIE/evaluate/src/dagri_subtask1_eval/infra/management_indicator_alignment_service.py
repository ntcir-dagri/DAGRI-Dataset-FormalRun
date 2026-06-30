from difflib import SequenceMatcher

from dagri_subtask1_eval.domain.management_indicator import ManagementIndicator
from dagri_subtask1_eval.domain.management_indicator_alignment_service import (
    ManagementIndicatorAlignment,
    ManagementIndicatorAlignmentService,
)


class SimilarityBasedManagementIndicatorAlignmentService(
    ManagementIndicatorAlignmentService
):
    def __init__(self, min_similarity: float = 0.6) -> None:
        self.min_similarity = min_similarity

    def align(
        self,
        submission_management_indicators: list[ManagementIndicator],
        eval_management_indicators: list[ManagementIndicator],
    ) -> list[ManagementIndicatorAlignment]:
        candidate_pairs: list[tuple[float, int, int]] = []
        for submission_index, submission_management_indicator in enumerate(
            submission_management_indicators
        ):
            for eval_index, eval_management_indicator in enumerate(eval_management_indicators):
                similarity = self._calculate_similarity(
                    submission_management_indicator.crop_name,
                    eval_management_indicator.crop_name,
                )
                if similarity >= self.min_similarity:
                    candidate_pairs.append((similarity, submission_index, eval_index))

        candidate_pairs.sort(key=lambda pair: (-pair[0], pair[1], pair[2]))

        aligned_eval_indices_by_submission_index: dict[int, tuple[int, float]] = {}
        used_eval_indices: set[int] = set()

        for similarity, submission_index, eval_index in candidate_pairs:
            if submission_index in aligned_eval_indices_by_submission_index:
                continue
            if eval_index in used_eval_indices:
                continue

            aligned_eval_indices_by_submission_index[submission_index] = (eval_index, similarity)
            used_eval_indices.add(eval_index)

        aligned_pairs: list[ManagementIndicatorAlignment] = []
        for submission_index, submission_management_indicator in enumerate(
            submission_management_indicators
        ):
            aligned_eval = aligned_eval_indices_by_submission_index.get(submission_index)
            aligned_pairs.append(
                ManagementIndicatorAlignment(
                    submission_management_indicator=submission_management_indicator,
                    eval_management_indicator=None
                    if aligned_eval is None
                    else eval_management_indicators[aligned_eval[0]],
                    similarity=0.0 if aligned_eval is None else aligned_eval[1],
                )
            )

        for eval_index, eval_management_indicator in enumerate(eval_management_indicators):
            if eval_index in used_eval_indices:
                continue
            aligned_pairs.append(
                ManagementIndicatorAlignment(
                    submission_management_indicator=None,
                    eval_management_indicator=eval_management_indicator,
                    similarity=0.0,
                )
            )

        return aligned_pairs

    @staticmethod
    def _calculate_similarity(name1: str, name2: str) -> float:
        return SequenceMatcher(None, name1.strip(), name2.strip()).ratio()
