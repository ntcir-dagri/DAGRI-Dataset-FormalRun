import logging
from pathlib import Path
from typing import Protocol

from dagri_subtask1_eval.domain.eval_dataset import EvalData, EvalDataset
from dagri_subtask1_eval.domain.management_indicator_alignment_service import (
    ManagementIndicatorAlignment,
    ManagementIndicatorAlignmentService,
)
from dagri_subtask1_eval.domain.management_indicators.balance_evaluation_service import (
    BalanceEvaluationService as ManagementIndicatorBalanceEvaluationService,
)
from dagri_subtask1_eval.domain.management_indicators.work_schedule_evaluation_service import (
    WorkScheduleEvaluationService,
)
from dagri_subtask1_eval.domain.management_indicators.work_technology_evaluation_service import (
    WorkTechnologyEvaluationService,
)
from dagri_subtask1_eval.domain.management_type_alignment_service import (
    ManagementTypeAlignment,
    ManagementTypeAlignmentService,
)
from dagri_subtask1_eval.domain.management_types.balance_evaluation_service import (
    BalanceEvaluationService as ManagementTypeBalanceEvaluationService,
)
from dagri_subtask1_eval.domain.management_types.capital_equipment_evaluation_service import (
    CapitalEquipmentEvaluationService,
)
from dagri_subtask1_eval.domain.management_types.growing_area_evaluation_service import (
    GrowingAreaEvaluationService,
)
from dagri_subtask1_eval.domain.management_types.premise_evaluation_service import (
    PremiseEvaluationService,
)
from dagri_subtask1_eval.domain.submission import Submission, SubmissionDataset


logger = logging.getLogger(__name__)


class SubmissionDatasetReader(Protocol):
    def read(self, file_path: str | Path) -> SubmissionDataset: ...


class EvalDatasetReader(Protocol):
    def read(self, file_path: str | Path) -> EvalDataset: ...


class EvaluateUsecase:
    def __init__(
        self,
        submission_dataset_reader: SubmissionDatasetReader,
        eval_dataset_reader: EvalDatasetReader,
        management_type_alignment_service: ManagementTypeAlignmentService,
        management_indicator_alignment_service: ManagementIndicatorAlignmentService,
        premise_evaluation_service: PremiseEvaluationService,
        management_type_balance_evaluation_service: ManagementTypeBalanceEvaluationService,
        growing_area_evaluation_service: GrowingAreaEvaluationService,
        capital_equipment_evaluation_service: CapitalEquipmentEvaluationService,
        management_indicator_balance_evaluation_service: ManagementIndicatorBalanceEvaluationService,
        work_schedule_evaluation_service: WorkScheduleEvaluationService,
        work_technology_evaluation_service: WorkTechnologyEvaluationService,
    ) -> None:
        self._submission_dataset_reader = submission_dataset_reader
        self._eval_dataset_reader = eval_dataset_reader
        self._management_type_alignment_service = management_type_alignment_service
        self._management_indicator_alignment_service = management_indicator_alignment_service
        self._premise_evaluation_service = premise_evaluation_service
        self._management_type_balance_evaluation_service = (
            management_type_balance_evaluation_service
        )
        self._growing_area_evaluation_service = growing_area_evaluation_service
        self._capital_equipment_evaluation_service = capital_equipment_evaluation_service
        self._management_indicator_balance_evaluation_service = (
            management_indicator_balance_evaluation_service
        )
        self._work_schedule_evaluation_service = work_schedule_evaluation_service
        self._work_technology_evaluation_service = work_technology_evaluation_service

    def execute(self, submission_file_path: str | Path, eval_file_path: str | Path) -> float:
        submission_dataset = self._submission_dataset_reader.read(submission_file_path)
        eval_dataset = self._eval_dataset_reader.read(eval_file_path)

        is_valid, missing_or_extra_keys = submission_dataset.validate_item_keys(eval_dataset)
        if not is_valid:
            raise ValueError(
                "提出データセットと正解データセットに含まれるサンプルが一致していません: "
                f"{missing_or_extra_keys}"
            )

        eval_items_by_key = {
            (item.prefecture_name, item.id): item for item in eval_dataset.items
        }

        scores: list[float] = []
        for submission_item in submission_dataset.items:
            eval_item = eval_items_by_key[(submission_item.prefecture_name, submission_item.id)]
            scores.extend(self._evaluate_submission(submission_item, eval_item))

        if not scores:
            logger.debug(
                "evaluation_completed",
                extra={"event_data": {"average_score": 0.0, "score_count": 0}},
            )
            return 0.0

        average_score = sum(scores) / len(scores)
        logger.info(
            "evaluation_completed",
            extra={
                "event_data": {
                    "average_score": average_score,
                    "score_count": len(scores),
                }
            },
        )
        return average_score

    def _evaluate_submission(
        self, submission_item: Submission, eval_item: EvalData
    ) -> list[float]:
        scores: list[float] = []

        for alignment in self._management_type_alignment_service.align(
            submission_item.management_types, eval_item.management_types
        ):
            scores.extend(self._evaluate_management_type_alignment(alignment))

        for alignment in self._management_indicator_alignment_service.align(
            submission_item.management_indicators, eval_item.management_indicators
        ):
            scores.extend(self._evaluate_management_indicator_alignment(alignment))

        return scores

    def _evaluate_management_type_alignment(
        self, alignment: ManagementTypeAlignment
    ) -> list[float]:
        if (
            alignment.submission_management_type is None
            or alignment.eval_management_type is None
        ):
            penalty_scores = self._zero_scores_for_unmatched_management_type(alignment)
            logger.debug(
                "management_type_alignment_unmatched",
                extra={
                    "event_data": {
                        "submission_management_type_id": None
                        if alignment.submission_management_type is None
                        else alignment.submission_management_type.id,
                        "eval_management_type_id": None
                        if alignment.eval_management_type is None
                        else alignment.eval_management_type.id,
                        "alignment_similarity": alignment.similarity,
                        "score": 0.0,
                        "unmatched_penalty_count": len(penalty_scores),
                    }
                },
            )
            return penalty_scores

        scores: list[float] = []
        scores.extend(
            self._log_field_evaluations(
                category="management_type",
                section="premise",
                submission_id=alignment.submission_management_type.id,
                eval_id=alignment.eval_management_type.id,
                alignment_similarity=alignment.similarity,
                evaluations=self._premise_evaluation_service.evaluate(
                    alignment.submission_management_type.premise,
                    alignment.eval_management_type.premise,
                ),
            )
        )
        scores.extend(
            self._log_field_evaluations(
                category="management_type",
                section="balance",
                submission_id=alignment.submission_management_type.id,
                eval_id=alignment.eval_management_type.id,
                alignment_similarity=alignment.similarity,
                evaluations=self._management_type_balance_evaluation_service.evaluate(
                    alignment.submission_management_type.balance,
                    alignment.eval_management_type.balance,
                ),
            )
        )
        scores.extend(
            self._log_field_evaluations(
                category="management_type",
                section="growing_area",
                submission_id=alignment.submission_management_type.id,
                eval_id=alignment.eval_management_type.id,
                alignment_similarity=alignment.similarity,
                evaluations=self._growing_area_evaluation_service.evaluate(
                    alignment.submission_management_type.growing_area,
                    alignment.eval_management_type.growing_area,
                ),
            )
        )
        scores.extend(
            self._log_field_evaluations(
                category="management_type",
                section="capital_equipment",
                submission_id=alignment.submission_management_type.id,
                eval_id=alignment.eval_management_type.id,
                alignment_similarity=alignment.similarity,
                evaluations=self._capital_equipment_evaluation_service.evaluate(
                    alignment.submission_management_type.capital_equipment,
                    alignment.eval_management_type.capital_equipment,
                ),
            )
        )
        return scores

    def _evaluate_management_indicator_alignment(
        self, alignment: ManagementIndicatorAlignment
    ) -> list[float]:
        if (
            alignment.submission_management_indicator is None
            or alignment.eval_management_indicator is None
        ):
            penalty_scores = self._zero_scores_for_unmatched_management_indicator(alignment)
            logger.debug(
                "management_indicator_alignment_unmatched",
                extra={
                    "event_data": {
                        "submission_management_indicator_id": None
                        if alignment.submission_management_indicator is None
                        else alignment.submission_management_indicator.id,
                        "eval_management_indicator_id": None
                        if alignment.eval_management_indicator is None
                        else alignment.eval_management_indicator.id,
                        "alignment_similarity": alignment.similarity,
                        "score": 0.0,
                        "unmatched_penalty_count": len(penalty_scores),
                    }
                },
            )
            return penalty_scores

        scores: list[float] = []
        scores.extend(
            self._log_field_evaluations(
                category="management_indicator",
                section="balance",
                submission_id=alignment.submission_management_indicator.id,
                eval_id=alignment.eval_management_indicator.id,
                alignment_similarity=alignment.similarity,
                evaluations=self._management_indicator_balance_evaluation_service.evaluate(
                    alignment.submission_management_indicator.balance,
                    alignment.eval_management_indicator.balance,
                ),
            )
        )
        scores.extend(
            self._log_field_evaluations(
                category="management_indicator",
                section="work_schedule",
                submission_id=alignment.submission_management_indicator.id,
                eval_id=alignment.eval_management_indicator.id,
                alignment_similarity=alignment.similarity,
                evaluations=self._work_schedule_evaluation_service.evaluate(
                    alignment.submission_management_indicator.work_schedule,
                    alignment.eval_management_indicator.work_schedule,
                ),
            )
        )
        scores.extend(
            self._log_field_evaluations(
                category="management_indicator",
                section="work_technology",
                submission_id=alignment.submission_management_indicator.id,
                eval_id=alignment.eval_management_indicator.id,
                alignment_similarity=alignment.similarity,
                evaluations=self._work_technology_evaluation_service.evaluate(
                    alignment.submission_management_indicator.work_technologies,
                    alignment.eval_management_indicator.work_technologies,
                ),
            )
        )
        return scores

    def _log_field_evaluations(
        self,
        category: str,
        section: str,
        submission_id: str,
        eval_id: str,
        alignment_similarity: float,
        evaluations: list[object],
    ) -> list[float]:
        scores: list[float] = []
        for evaluation in evaluations:
            logger.debug(
                "field_evaluation",
                extra={
                    "event_data": {
                        "category": category,
                        "section": section,
                        "submission_id": submission_id,
                        "eval_id": eval_id,
                        "alignment_similarity": alignment_similarity,
                        "field_name": evaluation.field_name,
                        "submission_value": evaluation.submission_value,
                        "eval_value": evaluation.eval_value,
                        "score": evaluation.score,
                    }
                },
            )
            scores.append(evaluation.score)
        return scores

    def _zero_scores_for_unmatched_management_type(
        self, alignment: ManagementTypeAlignment
    ) -> list[float]:
        reference_management_type = (
            alignment.eval_management_type
            if alignment.eval_management_type is not None
            else alignment.submission_management_type
        )
        if reference_management_type is None:
            return [0.0]

        penalty_count = 0
        penalty_count += len(
            self._premise_evaluation_service.evaluate(
                reference_management_type.premise, reference_management_type.premise
            )
        )
        penalty_count += len(
            self._management_type_balance_evaluation_service.evaluate(
                reference_management_type.balance, reference_management_type.balance
            )
        )
        penalty_count += len(
            self._growing_area_evaluation_service.evaluate(
                reference_management_type.growing_area, reference_management_type.growing_area
            )
        )
        penalty_count += len(
            self._capital_equipment_evaluation_service.evaluate(
                reference_management_type.capital_equipment,
                reference_management_type.capital_equipment,
            )
        )
        if penalty_count == 0:
            penalty_count = 1
        return [0.0] * penalty_count

    def _zero_scores_for_unmatched_management_indicator(
        self, alignment: ManagementIndicatorAlignment
    ) -> list[float]:
        reference_management_indicator = (
            alignment.eval_management_indicator
            if alignment.eval_management_indicator is not None
            else alignment.submission_management_indicator
        )
        if reference_management_indicator is None:
            return [0.0]

        penalty_count = 0
        penalty_count += len(
            self._management_indicator_balance_evaluation_service.evaluate(
                reference_management_indicator.balance, reference_management_indicator.balance
            )
        )
        penalty_count += len(
            self._work_schedule_evaluation_service.evaluate(
                reference_management_indicator.work_schedule,
                reference_management_indicator.work_schedule,
            )
        )
        penalty_count += len(
            self._work_technology_evaluation_service.evaluate(
                reference_management_indicator.work_technologies,
                reference_management_indicator.work_technologies,
            )
        )
        if penalty_count == 0:
            penalty_count = 1
        return [0.0] * penalty_count
