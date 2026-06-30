# DATA_SCHEMA

このドキュメントは、DAGRI Subtask 1 の提出データに含まれる「経営類型 (`ManagementType`)」「経営指標 (`ManagementIndicator`)」のデータ構造を定義します。

実装ソース:
- `src/dagri_subtask1_sdk/domain/management_type.py`
- `src/dagri_subtask1_sdk/domain/management_indicator.py`
- `src/dagri_subtask1_sdk/domain/management_types/*`
- `src/dagri_subtask1_sdk/domain/management_indicators/*`

## 1. 経営類型 (`ManagementType`)

### 1.1 フィールド

| フィールド名 | 型 | 必須 | 説明 |
|---|---|---|---|
| `id` | `str` | 必須 | 経営類型ID |
| `name` | `str` | 必須 | 経営類型名 |
| `premise` | `Premise` | 必須 | 前提表に関する情報 |
| `growing_area` | `GrowingAreaList` | 必須 | 栽培面積に関する情報 |
| `balance` | `Balance` | 必須 | この類型全体での経営収支表 |
| `capital_equipment` | `CapitalEquipmentList` | 必須 | この類型で使用する資本装備と減価償却に関する情報 |

### 1.2 前提表 `Premise`

| フィールド名 | 型 | 必須 | 説明 |
|---|---|---|---|
| `prefecture_name` | `str \| None` | 任意 | 都道府県名（フォルダの都道府県と一致させてください） |
| `area_name` | `str \| None` | 任意 | エリア名 |
| `crop_names` | `list[str] \| None` | 任意 | 栽培品目の名称一覧 |
| `cultivate_land` | `int \| None` | 任意 | 経営耕地の面積 |
| `cultivate_land_unit` | `str \| None` | 任意 | 経営耕地の面積単位 |
| `borrowed_cultivate_land` | `int \| None` | 任意 | 借入地の経営耕地面積 |
| `owned_cultivate_land` | `int \| None` | 任意 | 自作地の経営耕地面積 |
| `labor_raw` | `str \| None` | 任意 | 労働力 |
| `labors` | `float \| None` | 任意 | 労働力（数値に変換） |
| `total_income` | `int \| None` | 任意 | 総所得金額、目標所得額 |
| `total_labor_hours` | `float \| None` | 任意 | 総労働時間 |
| `note` | `str \| None` | 任意 | 備考 |

### 1.3 `GrowingAreaList` / `GrowingArea`

- `GrowingAreaList.items`: `list[GrowingArea] | None`

`GrowingArea`:

| フィールド名 | 型 | 必須 | 説明 |
|---|---|---|---|
| `crop_name` | `str \| None` | 任意 | 栽培品目名 |
| `cultivars` | `list[str] \| None` | 任意 | 品種名 |
| `area` | `int \| None` | 任意 | 栽培面積 |
| `area_unit` | `str \| None` | 任意 | 栽培面積単位 |

### 1.4 `CapitalEquipmentList` / `CapitalEquipment`

- `CapitalEquipmentList.items`: `list[CapitalEquipment] | None`

`CapitalEquipment`:

| フィールド名 | 型 | 必須 | 説明 |
|---|---|---|---|
| `item_name` | `str \| None` | 任意 | 資本設備名 |
| `amount` | `int \| float \| None` | 任意 | 数量 |
| `specification` | `str \| None` | 任意 | 仕様・特徴など |
| `acquisition_cost` | `int \| None` | 任意 | 取得金額 |
| `service_life` | `int \| None` | 任意 | 耐久年数 |
| `depreciation_cost` | `int \| None` | 任意 | 年間減価償却費用 |

### 1.5 `Balance`（経営類型）

`Balance` は以下の `float | None` と、対応する `_unit` の `str | None` を持ちます。

- `income`, `income_unit`
- `gross_revenue`, `gross_revenue_unit`
- `sales_revenue`, `sales_revenue_unit`
- `amount_of_yielding_main_product`, `amount_of_yielding_main_product_unit`
- `unit_price_main_product`, `unit_price_main_product_unit`
- `other_income`, `other_income_unit`
- `management_cost_total`, `management_cost_total_unit`
- `variable_cost_total`, `variable_cost_total_unit`
- `seedling_cost`, `seedling_cost_unit`
- `fertilizer_cost`, `fertilizer_cost_unit`
- `pesticide_cost`, `pesticide_cost_unit`
- `materials_cost`, `materials_cost_unit`
- `fuel_and_utilities_cost`, `fuel_and_utilities_cost_unit`
- `farm_tools_cost`, `farm_tools_cost_unit`
- `insurance_cost`, `insurance_cost_unit`
- `packing_freight_fees`, `packing_freight_fees_unit`
- `fixed_cost_total`, `fixed_cost_total_unit`
- `machinery_depreciation_cost`, `machinery_depreciation_cost_unit`
- `machinery_repair_cost`, `machinery_repair_cost_unit`
- `facility_depreciation_cost`, `facility_depreciation_cost_unit`
- `facility_repair_cost`, `facility_repair_cost_unit`
- `labor_cost`, `labor_cost_unit`
- `land_improvement_and_water_cost`, `land_improvement_and_water_cost_unit`
- `estimated_amount`, `estimated_amount_unit`
- `imputed_labor_cost`, `imputed_labor_cost_unit`
- `imputed_rent_paddy`, `imputed_rent_paddy_unit`
- `imputed_rent_upland`, `imputed_rent_upland_unit`
- `imputed_rent_orchard`, `imputed_rent_orchard_unit`
- `imputed_rent_greenhouse`, `imputed_rent_greenhouse_unit`
- `imputed_interest_on_capital`, `imputed_interest_on_capital_unit`
- `production_cost_before_byproduct_deduction`, `production_cost_before_byproduct_deduction_unit`

## 2. 経営指標 (`ManagementIndicator`)

### 2.1 フィールド

| フィールド名 | 型 | 必須 | 説明 |
|---|---|---|---|
| `id` | `str` | 必須 | 経営指標ID |
| `crop_name` | `str` | 必須 | 作目名 |
| `balance` | `Balance` | 必須 | 収支情報 |
| `work_schedule` | `WorkScheduleList` | 必須 | 作業暦情報 |
| `work_technologies` | `WorkTechnologyList` | 必須 | 作業技術情報 |

### 2.2 `Balance`（経営指標）

経営指標の `Balance` は、経営類型 `Balance` と同一のフィールド構成です。

### 2.3 `WorkScheduleList` / `WorkSchedule`

- `WorkScheduleList.term_unit`: `Literal["上下旬", "上中下旬"]`（必須）
- `WorkScheduleList.items`: `list[WorkSchedule] | None`

`WorkSchedule`:

| フィールド名 | 型 | 必須 | 説明 |
|---|---|---|---|
| `name` | `str \| None` | 任意 | 作業名 |
| `period` | `WorkSchedulePeriod \| None` | 任意 | 作業を実施する期 |
| `hours` | `float \| None` | 任意 | 指定の期における作業時間 |

`WorkSchedulePeriod` は以下の列挙値を取ります。

- `1月上旬`, `1月中旬`, `1月下旬`
- `2月上旬`, `2月中旬`, `2月下旬`
- `3月上旬`, `3月中旬`, `3月下旬`
- `4月上旬`, `4月中旬`, `4月下旬`
- `5月上旬`, `5月中旬`, `5月下旬`
- `6月上旬`, `6月中旬`, `6月下旬`
- `7月上旬`, `7月中旬`, `7月下旬`
- `8月上旬`, `8月中旬`, `8月下旬`
- `9月上旬`, `9月中旬`, `9月下旬`
- `10月上旬`, `10月中旬`, `10月下旬`
- `11月上旬`, `11月中旬`, `11月下旬`
- `12月上旬`, `12月中旬`, `12月下旬`

### 2.4 `WorkTechnologyList` / `WorkTechnology`

- `WorkTechnologyList.items`: `list[WorkTechnology] | None`

`WorkTechnology`:

| フィールド名 | 型 | 必須 | 説明 |
|---|---|---|---|
| `name` | `str \| None` | 任意 | 作業名 |
| `description` | `str \| None` | 任意 | 作業内容の説明 |
| `eqiupments` | `list[WorkTechnologyEquipment] \| None` | 任意 | 使用する機械設備一覧 |
| `materials` | `list[WorkTechnologyMaterial] \| None` | 任意 | 使用する資材一覧 |
| `number_of_workers` | `int \| None` | 任意 | 労働力 |
| `total_number_of_hours` | `float \| None` | 任意 | 総作業時間 |
| `cost` | `int \| None` | 任意 | 作業にかかり生じる支出 |
| `note` | `str \| None` | 任意 | 備考 |

> 注意: フィールド名は実装に合わせて `eqiupments`（スペルそのまま）です。

`WorkTechnologyEquipment`:

| フィールド名 | 型 | 必須 | 説明 |
|---|---|---|---|
| `name` | `str \| None` | 任意 | 機械設備名 |
| `hour` | `float \| None` | 任意 | 使用時間 |

`WorkTechnologyMaterial`:

| フィールド名 | 型 | 必須 | 説明 |
|---|---|---|---|
| `name` | `str \| None` | 任意 | 資材名 |
| `usage` | `str \| None` | 任意 | 使用量 |
| `usage_unit` | `str \| None` | 任意 | 使用量の単位 |

## 3. JSONL での格納イメージ

提出ファイルは 1 行に 1 サンプル（`Submission`）を格納する JSONL 形式です。
各行の `management_types` と `management_indicators` で、本ドキュメントの型を使用します。

```json
{
  "prefecture_name": "tokyo",
  "id": "sample-001",
  "management_types": [
    {
      "id": "mt-1",
      "name": "example-management-type",
      "premise": {},
      "growing_area": {"items": []},
      "balance": {},
      "capital_equipment": {"items": []}
    }
  ],
  "management_indicators": [
    {
      "id": "mi-1",
      "crop_name": "rice",
      "balance": {},
      "work_schedule": {"term_unit": "上下旬", "items": []},
      "work_technologies": {"items": []}
    }
  ]
}
```
