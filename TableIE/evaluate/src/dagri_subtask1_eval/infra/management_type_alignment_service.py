from difflib import SequenceMatcher

from dagri_subtask1_eval.domain.management_type import ManagementType
from dagri_subtask1_eval.domain.management_type_alignment_service import (
    ManagementTypeAlignment,
    ManagementTypeAlignmentService,
)


class SimilarityBasedManagementTypeAlignmentService(ManagementTypeAlignmentService):
    def __init__(self, min_similarity: float = 0.6) -> None:
        self.min_similarity = min_similarity

    def align(
        self,
        submission_management_types: list[ManagementType],
        eval_management_types: list[ManagementType],
    ) -> list[ManagementTypeAlignment]:
        candidate_pairs: list[tuple[float, int, int]] = []
        for submission_index, submission_management_type in enumerate(submission_management_types):
            for eval_index, eval_management_type in enumerate(eval_management_types):
                similarity = self._calculate_similarity(
                    submission_management_type.name, eval_management_type.name
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

        aligned_pairs: list[ManagementTypeAlignment] = []
        for submission_index, submission_management_type in enumerate(submission_management_types):
            aligned_eval = aligned_eval_indices_by_submission_index.get(submission_index)
            aligned_pairs.append(
                ManagementTypeAlignment(
                    submission_management_type=submission_management_type,
                    eval_management_type=None
                    if aligned_eval is None
                    else eval_management_types[aligned_eval[0]],
                    similarity=0.0 if aligned_eval is None else aligned_eval[1],
                )
            )

        for eval_index, eval_management_type in enumerate(eval_management_types):
            if eval_index in used_eval_indices:
                continue
            aligned_pairs.append(
                ManagementTypeAlignment(
                    submission_management_type=None,
                    eval_management_type=eval_management_type,
                    similarity=0.0,
                )
            )

        return aligned_pairs

    @staticmethod
    def _calculate_similarity(name1: str, name2: str) -> float:
        return SequenceMatcher(None, name1.strip(), name2.strip()).ratio()
