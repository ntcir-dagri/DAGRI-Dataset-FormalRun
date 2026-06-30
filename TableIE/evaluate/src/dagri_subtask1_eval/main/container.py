import os

from dagri_subtask1_eval.infra import (
    DefaultBalanceEvaluationService,
    DefaultCapitalEquipmentEvaluationService,
    DefaultGrowingAreaEvaluationService,
    DefaultManagementIndicatorBalanceEvaluationService,
    DefaultPremiseEvaluationService,
    DefaultWorkScheduleEvaluationService,
    DefaultWorkTechnologyEvaluationService,
    EvalDatasetReader,
    SimilarityBasedManagementIndicatorAlignmentService,
    SimilarityBasedManagementTypeAlignmentService,
    SubmissionDatasetReader,
)
from dagri_subtask1_eval.usecase.evaluate_usecase import EvaluateUsecase


def _get_similarity_threshold(env_name: str, default: float = 0.6) -> float:
    raw_value = os.getenv(env_name)
    if raw_value is None:
        return default

    try:
        threshold = float(raw_value)
    except ValueError as e:
        raise ValueError(f"{env_name} must be a float between 0.0 and 1.0") from e

    if not 0.0 <= threshold <= 1.0:
        raise ValueError(f"{env_name} must be between 0.0 and 1.0")
    return threshold


def build_evaluate_usecase() -> EvaluateUsecase:
    growing_area_min_similarity = _get_similarity_threshold(
        "DAGRI_GROWING_AREA_MIN_SIMILARITY"
    )
    capital_equipment_min_similarity = _get_similarity_threshold(
        "DAGRI_CAPITAL_EQUIPMENT_MIN_SIMILARITY"
    )
    work_schedule_min_similarity = _get_similarity_threshold(
        "DAGRI_WORK_SCHEDULE_MIN_SIMILARITY"
    )
    work_technology_min_item_similarity = _get_similarity_threshold(
        "DAGRI_WORK_TECHNOLOGY_MIN_ITEM_SIMILARITY"
    )
    work_technology_min_equipment_similarity = _get_similarity_threshold(
        "DAGRI_WORK_TECHNOLOGY_MIN_EQUIPMENT_SIMILARITY"
    )
    work_technology_min_material_similarity = _get_similarity_threshold(
        "DAGRI_WORK_TECHNOLOGY_MIN_MATERIAL_SIMILARITY"
    )

    return EvaluateUsecase(
        submission_dataset_reader=SubmissionDatasetReader(),
        eval_dataset_reader=EvalDatasetReader(),
        management_type_alignment_service=SimilarityBasedManagementTypeAlignmentService(),
        management_indicator_alignment_service=SimilarityBasedManagementIndicatorAlignmentService(),
        premise_evaluation_service=DefaultPremiseEvaluationService(),
        management_type_balance_evaluation_service=DefaultBalanceEvaluationService(),
        growing_area_evaluation_service=DefaultGrowingAreaEvaluationService(
            min_similarity=growing_area_min_similarity
        ),
        capital_equipment_evaluation_service=DefaultCapitalEquipmentEvaluationService(
            min_similarity=capital_equipment_min_similarity
        ),
        management_indicator_balance_evaluation_service=DefaultManagementIndicatorBalanceEvaluationService(),
        work_schedule_evaluation_service=DefaultWorkScheduleEvaluationService(
            min_similarity=work_schedule_min_similarity
        ),
        work_technology_evaluation_service=DefaultWorkTechnologyEvaluationService(
            min_item_similarity=work_technology_min_item_similarity,
            min_equipment_similarity=work_technology_min_equipment_similarity,
            min_material_similarity=work_technology_min_material_similarity,
        ),
    )
