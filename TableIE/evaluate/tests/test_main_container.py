import pytest

from dagri_subtask1_eval.usecase.evaluate_usecase import EvaluateUsecase
from dagri_subtask1_eval.main.container import build_evaluate_usecase


def test_build_evaluate_usecase_returns_usecase() -> None:
    usecase = build_evaluate_usecase()

    assert isinstance(usecase, EvaluateUsecase)


def test_build_evaluate_usecase_uses_default_similarity_thresholds(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("DAGRI_GROWING_AREA_MIN_SIMILARITY", raising=False)
    monkeypatch.delenv("DAGRI_CAPITAL_EQUIPMENT_MIN_SIMILARITY", raising=False)
    monkeypatch.delenv("DAGRI_WORK_SCHEDULE_MIN_SIMILARITY", raising=False)
    monkeypatch.delenv("DAGRI_WORK_TECHNOLOGY_MIN_ITEM_SIMILARITY", raising=False)
    monkeypatch.delenv("DAGRI_WORK_TECHNOLOGY_MIN_EQUIPMENT_SIMILARITY", raising=False)
    monkeypatch.delenv("DAGRI_WORK_TECHNOLOGY_MIN_MATERIAL_SIMILARITY", raising=False)

    usecase = build_evaluate_usecase()

    assert usecase._growing_area_evaluation_service._min_similarity == 0.6
    assert usecase._capital_equipment_evaluation_service._min_similarity == 0.6
    assert usecase._work_schedule_evaluation_service._min_similarity == 0.6
    assert usecase._work_technology_evaluation_service._min_item_similarity == 0.6
    assert usecase._work_technology_evaluation_service._min_equipment_similarity == 0.6
    assert usecase._work_technology_evaluation_service._min_material_similarity == 0.6


def test_build_evaluate_usecase_reads_similarity_thresholds_from_environment(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("DAGRI_GROWING_AREA_MIN_SIMILARITY", "0.71")
    monkeypatch.setenv("DAGRI_CAPITAL_EQUIPMENT_MIN_SIMILARITY", "0.72")
    monkeypatch.setenv("DAGRI_WORK_SCHEDULE_MIN_SIMILARITY", "0.73")
    monkeypatch.setenv("DAGRI_WORK_TECHNOLOGY_MIN_ITEM_SIMILARITY", "0.74")
    monkeypatch.setenv("DAGRI_WORK_TECHNOLOGY_MIN_EQUIPMENT_SIMILARITY", "0.75")
    monkeypatch.setenv("DAGRI_WORK_TECHNOLOGY_MIN_MATERIAL_SIMILARITY", "0.76")

    usecase = build_evaluate_usecase()

    assert usecase._growing_area_evaluation_service._min_similarity == 0.71
    assert usecase._capital_equipment_evaluation_service._min_similarity == 0.72
    assert usecase._work_schedule_evaluation_service._min_similarity == 0.73
    assert usecase._work_technology_evaluation_service._min_item_similarity == 0.74
    assert usecase._work_technology_evaluation_service._min_equipment_similarity == 0.75
    assert usecase._work_technology_evaluation_service._min_material_similarity == 0.76


def test_build_evaluate_usecase_rejects_invalid_similarity_threshold(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("DAGRI_GROWING_AREA_MIN_SIMILARITY", "not-a-number")

    with pytest.raises(ValueError, match="DAGRI_GROWING_AREA_MIN_SIMILARITY"):
        build_evaluate_usecase()
