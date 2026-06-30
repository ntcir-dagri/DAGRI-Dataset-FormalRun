from dagri_subtask1_eval.domain.management_indicators.work_schedule import (
    WorkSchedule,
    WorkScheduleList,
    WorkSchedulePeriod,
)
from dagri_subtask1_eval.infra.management_indicators.work_schedule_evaluation_service import (
    DefaultWorkScheduleEvaluationService,
)


def test_evaluate_returns_field_level_scores_for_aligned_items() -> None:
    service = DefaultWorkScheduleEvaluationService()
    submission_work_schedule = WorkScheduleList(
        term_unit="上中下旬",
        items=[
            WorkSchedule(name="播種", period=WorkSchedulePeriod.EARLY_JANUARY, hours=2.0),
            WorkSchedule(name="収穫", period=WorkSchedulePeriod.MID_FEBRUARY, hours=8.0),
        ],
    )
    eval_work_schedule = WorkScheduleList(
        term_unit="上中下旬",
        items=[
            WorkSchedule(name="収穫", period=WorkSchedulePeriod.MID_FEBRUARY, hours=10.0),
            WorkSchedule(name="播種", period=WorkSchedulePeriod.EARLY_JANUARY, hours=2.0),
        ],
    )

    evaluations = service.evaluate(submission_work_schedule, eval_work_schedule)
    evaluation_by_name = {evaluation.field_name: evaluation for evaluation in evaluations}

    assert evaluation_by_name["term_unit"].score == 1.0
    assert evaluation_by_name["items[0].name"].score == 1.0
    assert evaluation_by_name["items[0].period"].score == 1.0
    assert evaluation_by_name["items[0].hours"].score == 1.0
    assert evaluation_by_name["items[1].name"].score == 1.0
    assert evaluation_by_name["items[1].hours"].score == 0.0


def test_evaluate_returns_zero_scores_for_unmatched_items() -> None:
    service = DefaultWorkScheduleEvaluationService()
    submission_work_schedule = WorkScheduleList(
        term_unit="上中下旬",
        items=[WorkSchedule(name="播種", period=WorkSchedulePeriod.EARLY_JANUARY, hours=2.0)],
    )
    eval_work_schedule = WorkScheduleList(
        term_unit="上中下旬",
        items=[
            WorkSchedule(name="播種", period=WorkSchedulePeriod.EARLY_JANUARY, hours=2.0),
            WorkSchedule(name="施肥", period=WorkSchedulePeriod.MID_JANUARY, hours=1.0),
        ],
    )

    evaluations = service.evaluate(submission_work_schedule, eval_work_schedule)
    evaluation_by_name = {evaluation.field_name: evaluation for evaluation in evaluations}

    assert evaluation_by_name["items[1].name"].score == 0.0
    assert evaluation_by_name["items[1].period"].score == 0.0
    assert evaluation_by_name["items[1].hours"].score == 0.0


def test_evaluate_does_not_align_low_similarity_items() -> None:
    service = DefaultWorkScheduleEvaluationService(min_similarity=0.6)
    submission_work_schedule = WorkScheduleList(
        term_unit="上中下旬",
        items=[WorkSchedule(name="播種", period=WorkSchedulePeriod.EARLY_JANUARY, hours=2.0)],
    )
    eval_work_schedule = WorkScheduleList(
        term_unit="上中下旬",
        items=[WorkSchedule(name="収穫", period=WorkSchedulePeriod.LATE_DECEMBER, hours=8.0)],
    )

    evaluations = service.evaluate(submission_work_schedule, eval_work_schedule)
    evaluation_by_name = {evaluation.field_name: evaluation for evaluation in evaluations}

    assert evaluation_by_name["items[0].name"].score == 0.0
    assert evaluation_by_name["items[0].period"].score == 0.0
    assert evaluation_by_name["items[0].hours"].score == 0.0
    assert evaluation_by_name["items[1].name"].score == 0.0
    assert evaluation_by_name["items[1].period"].score == 0.0
    assert evaluation_by_name["items[1].hours"].score == 0.0
