from dagri_subtask1_eval.domain.management_indicators.balance import (
    Balance as ManagementIndicatorBalance,
)
from dagri_subtask1_eval.domain.management_indicators.work_schedule import (
    WorkSchedule,
    WorkScheduleList,
    WorkSchedulePeriod,
)
from dagri_subtask1_eval.domain.management_indicators.work_technologies import (
    WorkTechnology,
    WorkTechnologyEquipment,
    WorkTechnologyList,
    WorkTechnologyMaterial,
)
from dagri_subtask1_eval.domain.management_types.premise import Premise
from dagri_subtask1_eval.infra.management_indicators.balance_evaluation_service import (
    DefaultBalanceEvaluationService as DefaultManagementIndicatorBalanceEvaluationService,
)
from dagri_subtask1_eval.infra.management_indicators.work_schedule_evaluation_service import (
    DefaultWorkScheduleEvaluationService,
)
from dagri_subtask1_eval.infra.management_indicators.work_technology_evaluation_service import (
    DefaultWorkTechnologyEvaluationService,
)
from dagri_subtask1_eval.infra.management_types.premise_evaluation_service import (
    DefaultPremiseEvaluationService,
)


def test_premise_evaluation_uses_whitelisted_fields_only() -> None:
    service = DefaultPremiseEvaluationService(
        evaluated_fields=("prefecture_name", "cultivate_land")
    )

    evaluations = service.evaluate(
        Premise(prefecture_name="Tokyo", cultivate_land=10, note="ignored"),
        Premise(prefecture_name="Tokyo", cultivate_land=20, note="different"),
    )

    assert [evaluation.field_name for evaluation in evaluations] == [
        "prefecture_name",
        "cultivate_land",
    ]
    assert [evaluation.score for evaluation in evaluations] == [1.0, 0.0]


def test_management_indicator_balance_uses_whitelisted_fields_only() -> None:
    service = DefaultManagementIndicatorBalanceEvaluationService(
        evaluated_fields=("income",)
    )

    evaluations = service.evaluate(
        ManagementIndicatorBalance(income=100, income_unit="yen"),
        ManagementIndicatorBalance(income=100, income_unit="JPY"),
    )

    assert [evaluation.field_name for evaluation in evaluations] == ["income"]
    assert [evaluation.score for evaluation in evaluations] == [1.0]


def test_work_schedule_supports_independent_whitelists_for_root_and_items() -> None:
    service = DefaultWorkScheduleEvaluationService(
        evaluated_fields=(),
        evaluated_item_fields=("name",),
    )

    evaluations = service.evaluate(
        WorkScheduleList(
            term_unit="上下旬",
            items=[
                WorkSchedule(
                    name="播種",
                    period=WorkSchedulePeriod.EARLY_JANUARY,
                    hours=10,
                )
            ],
        ),
        WorkScheduleList(
            term_unit="上中下旬",
            items=[
                WorkSchedule(
                    name="播種",
                    period=WorkSchedulePeriod.LATE_JANUARY,
                    hours=20,
                )
            ],
        ),
    )

    assert [evaluation.field_name for evaluation in evaluations] == ["items[0].name"]
    assert [evaluation.score for evaluation in evaluations] == [1.0]


def test_work_technology_supports_nested_whitelists() -> None:
    service = DefaultWorkTechnologyEvaluationService(
        evaluated_item_fields=("name",),
        evaluated_equipment_fields=("name",),
        evaluated_material_fields=("usage",),
    )

    evaluations = service.evaluate(
        WorkTechnologyList(
            items=[
                WorkTechnology(
                    name="定植",
                    description="ignored",
                    number_of_workers=2,
                    eqiupments=[WorkTechnologyEquipment(name="トラクター", hour=4)],
                    materials=[
                        WorkTechnologyMaterial(name="肥料", usage="10", usage_unit="kg")
                    ],
                )
            ]
        ),
        WorkTechnologyList(
            items=[
                WorkTechnology(
                    name="定植",
                    description="different",
                    number_of_workers=5,
                    eqiupments=[WorkTechnologyEquipment(name="トラクター", hour=8)],
                    materials=[
                        WorkTechnologyMaterial(name="肥料", usage="10", usage_unit="袋")
                    ],
                )
            ]
        ),
    )

    assert [evaluation.field_name for evaluation in evaluations] == [
        "items[0].name",
        "items[0].eqiupments[0].name",
        "items[0].materials[0].usage",
    ]
    assert [evaluation.score for evaluation in evaluations] == [1.0, 1.0, 1.0]
