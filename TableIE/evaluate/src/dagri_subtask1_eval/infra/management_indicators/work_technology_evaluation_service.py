from dataclasses import dataclass
from difflib import SequenceMatcher
from typing import Iterable

from dagri_subtask1_eval.domain.management_indicators.work_technologies import (
    WorkTechnology,
    WorkTechnologyEquipment,
    WorkTechnologyMaterial,
)
from dagri_subtask1_eval.domain.management_indicators.work_technologies import (
    WorkTechnologyList,
)
from dagri_subtask1_eval.domain.management_indicators.work_technology_evaluation_service import (
    WorkTechnologyEvaluationService,
    WorkTechnologyFieldEvaluation,
)


@dataclass(frozen=True)
class _WorkTechnologyAlignment:
    submission_work_technology: WorkTechnology | None
    eval_work_technology: WorkTechnology | None


@dataclass(frozen=True)
class _WorkTechnologyEquipmentAlignment:
    submission_equipment: WorkTechnologyEquipment | None
    eval_equipment: WorkTechnologyEquipment | None


@dataclass(frozen=True)
class _WorkTechnologyMaterialAlignment:
    submission_material: WorkTechnologyMaterial | None
    eval_material: WorkTechnologyMaterial | None


class DefaultWorkTechnologyEvaluationService(WorkTechnologyEvaluationService):
    """アプリケーションで利用する作業技術一覧評価の標準実装ひな形。

    作業技術一覧は `WorkTechnology` の配列として表現されるため、
    評価ではまず提出データ側と正解データ側の各要素を対応付ける必要がある。
    想定する実装方針は次のとおり。

    1. `name` を主な手掛かりとして、必要に応じて `number_of_workers`、
       `total_number_of_hours`、`cost` を補助的に使い、提出側の要素と正解側の要素を
       1対1に対応付ける。
    2. 対応付けた要素どうしについて、基本項目に加えて `eqiupments` と `materials`
       のような入れ子の配列も段階的に評価する。
    3. 入れ子構造では、まず要素対応付けを行い、その後に各フィールドを個別評価する。
    4. 対応付けられなかった要素は未一致として扱い、関連する評価結果を 0 点寄りにする。
    5. 返り値は、後から要素単位・項目単位・入れ子単位で分析できる形を目指す。
    """

    DEFAULT_ITEM_FIELDS = (
        "name",
        "description",
        "number_of_workers",
        "total_number_of_hours",
        "cost",
        "note",
    )
    DEFAULT_EQUIPMENT_FIELDS = ("name", "hour")
    DEFAULT_MATERIAL_FIELDS = ("name", "usage", "usage_unit")

    def __init__(
        self,
        evaluated_item_fields: Iterable[str] | None = None,
        evaluated_equipment_fields: Iterable[str] | None = None,
        evaluated_material_fields: Iterable[str] | None = None,
        min_item_similarity: float = 0.6,
        min_equipment_similarity: float = 0.6,
        min_material_similarity: float = 0.6,
    ) -> None:
        self._evaluated_item_fields = tuple(
            self.DEFAULT_ITEM_FIELDS if evaluated_item_fields is None else evaluated_item_fields
        )
        self._evaluated_equipment_fields = tuple(
            self.DEFAULT_EQUIPMENT_FIELDS
            if evaluated_equipment_fields is None
            else evaluated_equipment_fields
        )
        self._evaluated_material_fields = tuple(
            self.DEFAULT_MATERIAL_FIELDS
            if evaluated_material_fields is None
            else evaluated_material_fields
        )
        self._min_item_similarity = min_item_similarity
        self._min_equipment_similarity = min_equipment_similarity
        self._min_material_similarity = min_material_similarity

    def evaluate(
        self,
        submission_work_technology: WorkTechnologyList,
        eval_work_technology: WorkTechnologyList,
    ) -> list[WorkTechnologyFieldEvaluation]:
        """上記方針に従って作業技術一覧の比較評価結果を返す。"""
        aligned_items = self._align_work_technologies(
            submission_work_technology.items or [], eval_work_technology.items or []
        )
        evaluations: list[WorkTechnologyFieldEvaluation] = []

        for index, aligned_item in enumerate(aligned_items):
            for field_name in self._evaluated_item_fields:
                evaluations.append(
                    self._create_field_evaluation(
                        prefix=f"items[{index}]",
                        field_name=field_name,
                        submission_value=None
                        if aligned_item.submission_work_technology is None
                        else getattr(aligned_item.submission_work_technology, field_name),
                        eval_value=None
                        if aligned_item.eval_work_technology is None
                        else getattr(aligned_item.eval_work_technology, field_name),
                    )
                )
            evaluations.extend(self._evaluate_equipments(index, aligned_item))
            evaluations.extend(self._evaluate_materials(index, aligned_item))

        return evaluations

    def _align_work_technologies(
        self,
        submission_items: list[WorkTechnology],
        eval_items: list[WorkTechnology],
    ) -> list[_WorkTechnologyAlignment]:
        candidate_pairs: list[tuple[float, int, int]] = []
        for submission_index, submission_item in enumerate(submission_items):
            for eval_index, eval_item in enumerate(eval_items):
                similarity = self._calculate_work_technology_similarity(
                    submission_item, eval_item
                )
                if similarity >= self._min_item_similarity:
                    candidate_pairs.append((similarity, submission_index, eval_index))

        return self._build_alignment(
            candidate_pairs,
            submission_items,
            eval_items,
            lambda submission_item, eval_item: _WorkTechnologyAlignment(
                submission_work_technology=submission_item,
                eval_work_technology=eval_item,
            ),
            lambda submission_item: _WorkTechnologyAlignment(
                submission_work_technology=submission_item,
                eval_work_technology=None,
            ),
            lambda eval_item: _WorkTechnologyAlignment(
                submission_work_technology=None,
                eval_work_technology=eval_item,
            ),
        )

    def _evaluate_equipments(
        self, work_technology_index: int, aligned_item: _WorkTechnologyAlignment
    ) -> list[WorkTechnologyFieldEvaluation]:
        submission_items = (
            []
            if aligned_item.submission_work_technology is None
            else aligned_item.submission_work_technology.eqiupments or []
        )
        eval_items = (
            []
            if aligned_item.eval_work_technology is None
            else aligned_item.eval_work_technology.eqiupments or []
        )
        aligned_equipments = self._align_equipments(submission_items, eval_items)

        evaluations: list[WorkTechnologyFieldEvaluation] = []
        for index, aligned_equipment in enumerate(aligned_equipments):
            prefix = f"items[{work_technology_index}].eqiupments[{index}]"
            for field_name in self._evaluated_equipment_fields:
                evaluations.append(
                    self._create_field_evaluation(
                        prefix=prefix,
                        field_name=field_name,
                        submission_value=None
                        if aligned_equipment.submission_equipment is None
                        else getattr(aligned_equipment.submission_equipment, field_name),
                        eval_value=None
                        if aligned_equipment.eval_equipment is None
                        else getattr(aligned_equipment.eval_equipment, field_name),
                    )
                )
        return evaluations

    def _evaluate_materials(
        self, work_technology_index: int, aligned_item: _WorkTechnologyAlignment
    ) -> list[WorkTechnologyFieldEvaluation]:
        submission_items = (
            []
            if aligned_item.submission_work_technology is None
            else aligned_item.submission_work_technology.materials or []
        )
        eval_items = (
            []
            if aligned_item.eval_work_technology is None
            else aligned_item.eval_work_technology.materials or []
        )
        aligned_materials = self._align_materials(submission_items, eval_items)

        evaluations: list[WorkTechnologyFieldEvaluation] = []
        for index, aligned_material in enumerate(aligned_materials):
            prefix = f"items[{work_technology_index}].materials[{index}]"
            for field_name in self._evaluated_material_fields:
                evaluations.append(
                    self._create_field_evaluation(
                        prefix=prefix,
                        field_name=field_name,
                        submission_value=None
                        if aligned_material.submission_material is None
                        else getattr(aligned_material.submission_material, field_name),
                        eval_value=None
                        if aligned_material.eval_material is None
                        else getattr(aligned_material.eval_material, field_name),
                    )
                )
        return evaluations

    def _align_equipments(
        self,
        submission_items: list[WorkTechnologyEquipment],
        eval_items: list[WorkTechnologyEquipment],
    ) -> list[_WorkTechnologyEquipmentAlignment]:
        candidate_pairs: list[tuple[float, int, int]] = []
        for submission_index, submission_item in enumerate(submission_items):
            for eval_index, eval_item in enumerate(eval_items):
                similarity = self._calculate_equipment_similarity(submission_item, eval_item)
                if similarity >= self._min_equipment_similarity:
                    candidate_pairs.append((similarity, submission_index, eval_index))

        return self._build_alignment(
            candidate_pairs,
            submission_items,
            eval_items,
            lambda submission_item, eval_item: _WorkTechnologyEquipmentAlignment(
                submission_equipment=submission_item,
                eval_equipment=eval_item,
            ),
            lambda submission_item: _WorkTechnologyEquipmentAlignment(
                submission_equipment=submission_item,
                eval_equipment=None,
            ),
            lambda eval_item: _WorkTechnologyEquipmentAlignment(
                submission_equipment=None,
                eval_equipment=eval_item,
            ),
        )

    def _align_materials(
        self,
        submission_items: list[WorkTechnologyMaterial],
        eval_items: list[WorkTechnologyMaterial],
    ) -> list[_WorkTechnologyMaterialAlignment]:
        candidate_pairs: list[tuple[float, int, int]] = []
        for submission_index, submission_item in enumerate(submission_items):
            for eval_index, eval_item in enumerate(eval_items):
                similarity = self._calculate_material_similarity(submission_item, eval_item)
                if similarity >= self._min_material_similarity:
                    candidate_pairs.append((similarity, submission_index, eval_index))

        return self._build_alignment(
            candidate_pairs,
            submission_items,
            eval_items,
            lambda submission_item, eval_item: _WorkTechnologyMaterialAlignment(
                submission_material=submission_item,
                eval_material=eval_item,
            ),
            lambda submission_item: _WorkTechnologyMaterialAlignment(
                submission_material=submission_item,
                eval_material=None,
            ),
            lambda eval_item: _WorkTechnologyMaterialAlignment(
                submission_material=None,
                eval_material=eval_item,
            ),
        )

    @staticmethod
    def _build_alignment(
        candidate_pairs: list[tuple[float, int, int]],
        submission_items: list[object],
        eval_items: list[object],
        matched_factory,
        submission_only_factory,
        eval_only_factory,
    ) -> list[object]:
        candidate_pairs.sort(key=lambda pair: (-pair[0], pair[1], pair[2]))

        aligned_eval_indices_by_submission_index: dict[int, int] = {}
        used_eval_indices: set[int] = set()

        for _, submission_index, eval_index in candidate_pairs:
            if submission_index in aligned_eval_indices_by_submission_index:
                continue
            if eval_index in used_eval_indices:
                continue

            aligned_eval_indices_by_submission_index[submission_index] = eval_index
            used_eval_indices.add(eval_index)

        aligned_items: list[object] = []
        for submission_index, submission_item in enumerate(submission_items):
            eval_index = aligned_eval_indices_by_submission_index.get(submission_index)
            if eval_index is None:
                aligned_items.append(submission_only_factory(submission_item))
            else:
                aligned_items.append(matched_factory(submission_item, eval_items[eval_index]))

        for eval_index, eval_item in enumerate(eval_items):
            if eval_index in used_eval_indices:
                continue
            aligned_items.append(eval_only_factory(eval_item))

        return aligned_items

    def _calculate_work_technology_similarity(
        self, submission_item: WorkTechnology, eval_item: WorkTechnology
    ) -> float:
        scores = [
            self._evaluate_field(
                getattr(submission_item, field_name), getattr(eval_item, field_name)
            )
            for field_name in self._evaluated_item_fields
        ]
        if not scores:
            return 0.0
        return sum(scores) / len(scores)

    def _calculate_equipment_similarity(
        self,
        submission_item: WorkTechnologyEquipment,
        eval_item: WorkTechnologyEquipment,
    ) -> float:
        scores = [
            self._evaluate_field(
                getattr(submission_item, field_name), getattr(eval_item, field_name)
            )
            for field_name in self._evaluated_equipment_fields
        ]
        if not scores:
            return 0.0
        return sum(scores) / len(scores)

    def _calculate_material_similarity(
        self,
        submission_item: WorkTechnologyMaterial,
        eval_item: WorkTechnologyMaterial,
    ) -> float:
        scores = [
            self._evaluate_field(
                getattr(submission_item, field_name), getattr(eval_item, field_name)
            )
            for field_name in self._evaluated_material_fields
        ]
        if not scores:
            return 0.0
        return sum(scores) / len(scores)

    def _create_field_evaluation(
        self,
        prefix: str,
        field_name: str,
        submission_value: object,
        eval_value: object,
    ) -> WorkTechnologyFieldEvaluation:
        return WorkTechnologyFieldEvaluation(
            field_name=f"{prefix}.{field_name}",
            submission_value=submission_value,
            eval_value=eval_value,
            score=self._evaluate_field(submission_value, eval_value),
        )

    def _evaluate_field(self, submission_value: object, eval_value: object) -> float:
        if isinstance(submission_value, (int, float)) or isinstance(eval_value, (int, float)):
            return self._evaluate_numeric(submission_value, eval_value)
        return self._evaluate_string(submission_value, eval_value)

    @staticmethod
    def _evaluate_string(submission_value: object, eval_value: object) -> float:
        if submission_value is None and eval_value is None:
            return 1.0
        if submission_value is None or eval_value is None:
            return 0.0
        return SequenceMatcher(
            None, str(submission_value).strip(), str(eval_value).strip()
        ).ratio()

    @staticmethod
    def _evaluate_numeric(submission_value: object, eval_value: object) -> float:
        if submission_value is None and eval_value is None:
            return 1.0
        if submission_value is None or eval_value is None:
            return 0.0
        return 1.0 if submission_value == eval_value else 0.0
