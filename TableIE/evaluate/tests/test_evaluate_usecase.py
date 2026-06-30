from pathlib import Path

from dagri_subtask1_eval.domain.eval_dataset import EvalData, EvalDataset
from dagri_subtask1_eval.domain.management_indicator import ManagementIndicator
from dagri_subtask1_eval.domain.management_indicator_alignment_service import (
    ManagementIndicatorAlignment,
)
from dagri_subtask1_eval.domain.management_indicators.balance import Balance as IndicatorBalance
from dagri_subtask1_eval.domain.management_indicators.balance_evaluation_service import (
    BalanceFieldEvaluation as IndicatorBalanceFieldEvaluation,
)
from dagri_subtask1_eval.domain.management_indicators.work_schedule import WorkScheduleList
from dagri_subtask1_eval.domain.management_indicators.work_schedule_evaluation_service import (
    WorkScheduleFieldEvaluation,
)
from dagri_subtask1_eval.domain.management_indicators.work_technologies import (
    WorkTechnologyList,
)
from dagri_subtask1_eval.domain.management_indicators.work_technology_evaluation_service import (
    WorkTechnologyFieldEvaluation,
)
from dagri_subtask1_eval.domain.management_type import ManagementType
from dagri_subtask1_eval.domain.management_type_alignment_service import (
    ManagementTypeAlignment,
)
from dagri_subtask1_eval.domain.management_types.balance import Balance as TypeBalance
from dagri_subtask1_eval.domain.management_types.balance_evaluation_service import (
    BalanceFieldEvaluation as TypeBalanceFieldEvaluation,
)
from dagri_subtask1_eval.domain.management_types.capital_equipment import (
    CapitalEquipmentList,
)
from dagri_subtask1_eval.domain.management_types.capital_equipment_evaluation_service import (
    CapitalEquipmentFieldEvaluation,
)
from dagri_subtask1_eval.domain.management_types.growing_area import GrowingAreaList
from dagri_subtask1_eval.domain.management_types.growing_area_evaluation_service import (
    GrowingAreaFieldEvaluation,
)
from dagri_subtask1_eval.domain.management_types.premise import Premise
from dagri_subtask1_eval.domain.management_types.premise_evaluation_service import (
    PremiseFieldEvaluation,
)
from dagri_subtask1_eval.domain.submission import Submission, SubmissionDataset
from dagri_subtask1_eval.usecase.evaluate_usecase import EvaluateUsecase


class StubSubmissionDatasetReader:
    def __init__(self, dataset: SubmissionDataset) -> None:
        self.dataset = dataset
        self.read_calls: list[str | Path] = []

    def read(self, file_path: str | Path) -> SubmissionDataset:
        self.read_calls.append(file_path)
        return self.dataset


class StubEvalDatasetReader:
    def __init__(self, dataset: EvalDataset) -> None:
        self.dataset = dataset
        self.read_calls: list[str | Path] = []

    def read(self, file_path: str | Path) -> EvalDataset:
        self.read_calls.append(file_path)
        return self.dataset


class StubManagementTypeAlignmentService:
    def __init__(self, alignments: list[ManagementTypeAlignment]) -> None:
        self.alignments = alignments

    def align(
        self,
        submission_management_types: list[ManagementType],
        eval_management_types: list[ManagementType],
    ) -> list[ManagementTypeAlignment]:
        return self.alignments


class StubManagementIndicatorAlignmentService:
    def __init__(self, alignments: list[ManagementIndicatorAlignment]) -> None:
        self.alignments = alignments

    def align(
        self,
        submission_management_indicators: list[ManagementIndicator],
        eval_management_indicators: list[ManagementIndicator],
    ) -> list[ManagementIndicatorAlignment]:
        return self.alignments


class StubPremiseEvaluationService:
    def __init__(self, scores: list[float]) -> None:
        self.scores = scores

    def evaluate(self, submission_premise: Premise, eval_premise: Premise) -> list[PremiseFieldEvaluation]:
        return [
            PremiseFieldEvaluation(
                field_name=f"premise_{index}",
                submission_value=None,
                eval_value=None,
                score=score,
            )
            for index, score in enumerate(self.scores)
        ]


class StubManagementTypeBalanceEvaluationService:
    def __init__(self, scores: list[float]) -> None:
        self.scores = scores

    def evaluate(
        self, submission_balance: TypeBalance, eval_balance: TypeBalance
    ) -> list[TypeBalanceFieldEvaluation]:
        return [
            TypeBalanceFieldEvaluation(
                field_name=f"type_balance_{index}",
                submission_value=None,
                eval_value=None,
                score=score,
            )
            for index, score in enumerate(self.scores)
        ]


class StubGrowingAreaEvaluationService:
    def __init__(self, scores: list[float]) -> None:
        self.scores = scores

    def evaluate(
        self,
        submission_growing_area: GrowingAreaList,
        eval_growing_area: GrowingAreaList,
    ) -> list[GrowingAreaFieldEvaluation]:
        return [
            GrowingAreaFieldEvaluation(
                field_name=f"growing_area_{index}",
                submission_value=None,
                eval_value=None,
                score=score,
            )
            for index, score in enumerate(self.scores)
        ]


class StubCapitalEquipmentEvaluationService:
    def __init__(self, scores: list[float]) -> None:
        self.scores = scores

    def evaluate(
        self,
        submission_capital_equipment: CapitalEquipmentList,
        eval_capital_equipment: CapitalEquipmentList,
    ) -> list[CapitalEquipmentFieldEvaluation]:
        return [
            CapitalEquipmentFieldEvaluation(
                field_name=f"capital_equipment_{index}",
                submission_value=None,
                eval_value=None,
                score=score,
            )
            for index, score in enumerate(self.scores)
        ]


class StubManagementIndicatorBalanceEvaluationService:
    def __init__(self, scores: list[float]) -> None:
        self.scores = scores

    def evaluate(
        self, submission_balance: IndicatorBalance, eval_balance: IndicatorBalance
    ) -> list[IndicatorBalanceFieldEvaluation]:
        return [
            IndicatorBalanceFieldEvaluation(
                field_name=f"indicator_balance_{index}",
                submission_value=None,
                eval_value=None,
                score=score,
            )
            for index, score in enumerate(self.scores)
        ]


class StubWorkScheduleEvaluationService:
    def __init__(self, scores: list[float]) -> None:
        self.scores = scores

    def evaluate(
        self,
        submission_work_schedule: WorkScheduleList,
        eval_work_schedule: WorkScheduleList,
    ) -> list[WorkScheduleFieldEvaluation]:
        return [
            WorkScheduleFieldEvaluation(
                field_name=f"work_schedule_{index}",
                submission_value=None,
                eval_value=None,
                score=score,
            )
            for index, score in enumerate(self.scores)
        ]


class StubWorkTechnologyEvaluationService:
    def __init__(self, scores: list[float]) -> None:
        self.scores = scores

    def evaluate(
        self,
        submission_work_technology: WorkTechnologyList,
        eval_work_technology: WorkTechnologyList,
    ) -> list[WorkTechnologyFieldEvaluation]:
        return [
            WorkTechnologyFieldEvaluation(
                field_name=f"work_technology_{index}",
                submission_value=None,
                eval_value=None,
                score=score,
            )
            for index, score in enumerate(self.scores)
        ]


def test_execute_returns_average_score_when_samples_match() -> None:
    submission = create_submission("tokyo", "1")
    eval_data = create_eval_data("tokyo", "1")

    usecase = EvaluateUsecase(
        submission_dataset_reader=StubSubmissionDatasetReader(SubmissionDataset(items=[submission])),
        eval_dataset_reader=StubEvalDatasetReader(EvalDataset(items=[eval_data])),
        management_type_alignment_service=StubManagementTypeAlignmentService(
            [
                ManagementTypeAlignment(
                    submission_management_type=submission.management_types[0],
                    eval_management_type=eval_data.management_types[0],
                    similarity=1.0,
                ),
                ManagementTypeAlignment(
                    submission_management_type=None,
                    eval_management_type=eval_data.management_types[1],
                    similarity=0.0,
                ),
            ]
        ),
        management_indicator_alignment_service=StubManagementIndicatorAlignmentService(
            [
                ManagementIndicatorAlignment(
                    submission_management_indicator=submission.management_indicators[0],
                    eval_management_indicator=eval_data.management_indicators[0],
                    similarity=1.0,
                )
            ]
        ),
        premise_evaluation_service=StubPremiseEvaluationService([1.0, 0.5]),
        management_type_balance_evaluation_service=StubManagementTypeBalanceEvaluationService([0.5]),
        growing_area_evaluation_service=StubGrowingAreaEvaluationService([1.0]),
        capital_equipment_evaluation_service=StubCapitalEquipmentEvaluationService([0.0]),
        management_indicator_balance_evaluation_service=StubManagementIndicatorBalanceEvaluationService(
            [0.5]
        ),
        work_schedule_evaluation_service=StubWorkScheduleEvaluationService([1.0]),
        work_technology_evaluation_service=StubWorkTechnologyEvaluationService([0.0]),
    )

    score = usecase.execute("submission.jsonl", "eval.jsonl")

    assert score == 4.5 / 13


def test_execute_raises_error_when_samples_do_not_match() -> None:
    submission = create_submission("tokyo", "1")
    eval_data = create_eval_data("osaka", "2")

    usecase = EvaluateUsecase(
        submission_dataset_reader=StubSubmissionDatasetReader(SubmissionDataset(items=[submission])),
        eval_dataset_reader=StubEvalDatasetReader(EvalDataset(items=[eval_data])),
        management_type_alignment_service=StubManagementTypeAlignmentService([]),
        management_indicator_alignment_service=StubManagementIndicatorAlignmentService([]),
        premise_evaluation_service=StubPremiseEvaluationService([]),
        management_type_balance_evaluation_service=StubManagementTypeBalanceEvaluationService([]),
        growing_area_evaluation_service=StubGrowingAreaEvaluationService([]),
        capital_equipment_evaluation_service=StubCapitalEquipmentEvaluationService([]),
        management_indicator_balance_evaluation_service=StubManagementIndicatorBalanceEvaluationService(
            []
        ),
        work_schedule_evaluation_service=StubWorkScheduleEvaluationService([]),
        work_technology_evaluation_service=StubWorkTechnologyEvaluationService([]),
    )

    try:
        usecase.execute("submission.jsonl", "eval.jsonl")
    except ValueError as e:
        assert "含まれるサンプルが一致していません" in str(e)
    else:
        raise AssertionError("ValueError was not raised")


def test_execute_adds_field_count_penalty_for_unmatched_management_type() -> None:
    submission = create_submission("tokyo", "1")
    eval_data = create_eval_data("tokyo", "1")

    usecase = EvaluateUsecase(
        submission_dataset_reader=StubSubmissionDatasetReader(SubmissionDataset(items=[submission])),
        eval_dataset_reader=StubEvalDatasetReader(EvalDataset(items=[eval_data])),
        management_type_alignment_service=StubManagementTypeAlignmentService(
            [
                ManagementTypeAlignment(
                    submission_management_type=None,
                    eval_management_type=eval_data.management_types[0],
                    similarity=0.0,
                )
            ]
        ),
        management_indicator_alignment_service=StubManagementIndicatorAlignmentService([]),
        premise_evaluation_service=StubPremiseEvaluationService([1.0, 1.0]),
        management_type_balance_evaluation_service=StubManagementTypeBalanceEvaluationService([1.0]),
        growing_area_evaluation_service=StubGrowingAreaEvaluationService([1.0]),
        capital_equipment_evaluation_service=StubCapitalEquipmentEvaluationService([1.0]),
        management_indicator_balance_evaluation_service=StubManagementIndicatorBalanceEvaluationService(
            []
        ),
        work_schedule_evaluation_service=StubWorkScheduleEvaluationService([]),
        work_technology_evaluation_service=StubWorkTechnologyEvaluationService([]),
    )

    score = usecase.execute("submission.jsonl", "eval.jsonl")

    assert score == 0.0


def test_execute_adds_field_count_penalty_for_unmatched_management_indicator() -> None:
    submission = create_submission("tokyo", "1")
    eval_data = create_eval_data("tokyo", "1")

    usecase = EvaluateUsecase(
        submission_dataset_reader=StubSubmissionDatasetReader(SubmissionDataset(items=[submission])),
        eval_dataset_reader=StubEvalDatasetReader(EvalDataset(items=[eval_data])),
        management_type_alignment_service=StubManagementTypeAlignmentService([]),
        management_indicator_alignment_service=StubManagementIndicatorAlignmentService(
            [
                ManagementIndicatorAlignment(
                    submission_management_indicator=None,
                    eval_management_indicator=eval_data.management_indicators[0],
                    similarity=0.0,
                )
            ]
        ),
        premise_evaluation_service=StubPremiseEvaluationService([]),
        management_type_balance_evaluation_service=StubManagementTypeBalanceEvaluationService([]),
        growing_area_evaluation_service=StubGrowingAreaEvaluationService([]),
        capital_equipment_evaluation_service=StubCapitalEquipmentEvaluationService([]),
        management_indicator_balance_evaluation_service=StubManagementIndicatorBalanceEvaluationService(
            [1.0, 1.0]
        ),
        work_schedule_evaluation_service=StubWorkScheduleEvaluationService([1.0]),
        work_technology_evaluation_service=StubWorkTechnologyEvaluationService([1.0, 1.0, 1.0]),
    )

    score = usecase.execute("submission.jsonl", "eval.jsonl")

    assert score == 0.0


def create_submission(prefecture_name: str, id: str) -> Submission:
    return Submission(
        prefecture_name=prefecture_name,
        id=id,
        management_types=[create_management_type("mt1", "たまねぎ")],
        management_indicators=[create_management_indicator("mi1", "たまねぎ")],
    )


def create_eval_data(prefecture_name: str, id: str) -> EvalData:
    return EvalData(
        prefecture_name=prefecture_name,
        id=id,
        management_types=[
            create_management_type("mt1", "たまねぎ"),
            create_management_type("mt2", "みかん"),
        ],
        management_indicators=[create_management_indicator("mi1", "たまねぎ")],
    )


def create_management_type(id: str, name: str) -> ManagementType:
    return ManagementType(
        id=id,
        name=name,
        premise=Premise(),
        growing_area=GrowingAreaList(items=[]),
        balance=TypeBalance(),
        capital_equipment=CapitalEquipmentList(items=[]),
    )


def create_management_indicator(id: str, crop_name: str) -> ManagementIndicator:
    return ManagementIndicator(
        id=id,
        crop_name=crop_name,
        balance=IndicatorBalance(),
        work_schedule=WorkScheduleList(term_unit="上中下旬", items=[]),
        work_technologies=WorkTechnologyList(items=[]),
    )
