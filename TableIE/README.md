# Subtask 1: Table IE 

Subtask 1では、各都道府県の農業技術文書から経営類型・経営指標に関する情報を抽出・構造化することを目指します。

配布データは以下の通りとなります。

* `train/input/{都道府県名}/`: 訓練セット（農業技術文書と、抽出・構造化のタスク仕様書）
    * `train/input/{都道府県名}/urls.txt`: 農業技術文書のPDFリンク集になります。適宜ダウンロードをしてください（ダウンロードスクリプト `download.sh` を用意しています）
    * `train/input/{都道府県名}/Instructions.md`: 抽出・構造化を行うときのファイル仕様や注意点などをまとめたドキュメントになります
* `train/output.jsonl`: 訓練セットにに対する情報抽出・構造化の結果
    * 訓練・ファインチューニング、データ理解のために使用してください
    * JSONL形式となっており、提出するときのファイルフォーマットに従っています
    * `train/input/{{.prefecture_name}}/{{.id}}.pdf` で入力したPDFファイルを解決できる仕様となっています
* `test/input/{都道府県名}/`: 評価セット（農業技術文書と、抽出・構造化のタスク仕様書）
    * `test/input/{都道府県名}/urls.txt`: 農業技術文書のPDFリンク集になります。適宜ダウンロードをしてください（ダウンロードスクリプト `download.sh` を用意しています）
    * `test/input/{都道府県名}/Instructions.md`: 抽出・構造化を行うときのファイル仕様や注意点などをまとめたドキュメントになります


# 提出ファイルのフォーマット

評価セットに対する情報抽出・構造化の結果について、1つの農業技術文書につき、抽出/構造化した結果を1行のJSON（JSONL形式）で出力してください。
JSON仕様は以下となります。また配布している `train/output.jsonl` は提出時のフォーマットとなっていますので、あわせて参照してください。

* `prefecture_name`: 都道府県名で、評価データの入力ディレクトリの名前 `test/input/{{.prefecture_name}}` の `{{.prefecture_name}}` 箇所を想定しています。
* `id`: 農業技術文書のファイルID（ファイル名から拡張子を除いたもの）で、 `test/input/{{.prefecture_name}}/{{.id}}.pdf` の `{{.id}}` 箇所を想定しています。
* `management_types`: 抽出・構造化できた経営類型
* `management_indicators`: 抽出・構造化できた経営指標

## 経営類型のデータ型

1つの農業技術文書には複数の経営類型が記述している可能性があります。
すべて抽出して以下に定義するJSONオブジェクトとして書き出してください。

* `id`: 類型名（なんでもよいです; 評価には直接使用しません）
* `name`: 類型名
* `premise`: 前提表
* `growing_area`: 栽培面積
* `balance`: 経営収支表
* `capital_equipment`: 資本設備と減価償却費用

経営類型は、前提表 `premise` と栽培面積 `growing_area` 、経営収支表 `balance` 、資本設備と減価償却費用 `capital_equipment` の4つから構成されます。
各項目の定義/スキーマを以下に記述します。

### 前提表

類型（モデル）の前提条件に関する情報となります。以下のフィールドを持つJSONオブジェクトとなります。
すべて任意キー（null許容）で、農業技術文書に記載があれば適当な型で値をセットし、記載が無ければ `null` としてください。

| フィールド名 | 型 | 説明 |
|---|---|---|
| `prefecture_name` | `str` | 都道府県名 |
| `area_name` | `str` |  |
| `crop_names` | `list[str]` | この類型で栽培する作物の名称一覧 |
| `cultivate_land` | `int` | 経営耕地面積 |
| `cultivate_land_unit` | `str` | 経営耕地面積の単位 |
| `borrowed_cultivate_land` | `int` | 経営耕地のうち、借入地・借地に該当する面積 |
| `owned_cultivate_land` | `int` | 借入地に該当する面積の単位 |
| `labor_raw` | `str` | 経営耕地のうち、自作地に該当する面積 |
| `labors` | `float` | 自作地に該当する面積の単位 |
| `total_income` | `int` | この類型における総所得金額 |
| `total_labor_hours` | `float` | この類型における労働時間 |
| `note` | `str` | 備考欄 |

### 栽培面積

類型にて栽培する作物とその規模に関する情報となります。1類型で複数の作物を栽培することがありますので、
`.items` という配列内に、各作物に関する栽培規模を表すJSONオブジェクトをセットしてください。
各作物に関する栽培規模を表すJSONオブジェクトの定義は以下となります。
すべて任意キー（null許容）で、農業技術文書に記載があれば適当な型で値をセットし、記載が無ければ `null` としてください。

| フィールド名 | 型 | 説明 |
|---|---|---|
| `crop_name` | `str` | 栽培の対象となる作物の名称 |
| `cultivars` | `list[str]` | 品目名 `crop_name` の品種名 |
| `area` | `int` | 品目名 `crop_name` の栽培面積 |
| `area_unit` | `str` | 品目名 `crop_name` の栽培面積の単位 |

### 経営収支表

類型で設定した目標所得金額の根拠となる収支表となります。
収入、支出項目は以下となります。金額はすべて `float` 型としています。
また各収入、支出の項目の後ろに `_unit` とついた `str`型のフィールド名がありますが、これはそれぞれの項目の単位系を表しています。

- 所得 `income`: 
- 粗収益 `gross_revenue`:
- 販売収入 `sales_revenue`:
- 収量（主産物） `amount_of_yielding_main_product`:
- 単価（主産物） `unit_price_main_product`: 
- その他収入（副産物、交付金など） `other_income`: 
- 経営費計 `management_cost_total`:
- 変動費計 `variable_cost_total`:
- 種苗費 `seedling_cost`:
- 肥料費 `fertilizer_cost`:
- 農薬費 `pesticide_cost`:
- 諸材料費 `materials_cost`:
- 動力光熱費 `fuel_and_utilities_cost`:
- 農具費 `farm_tools_cost`:
- 共済費 `insurance_cost`:
- 荷造運賃手数料 `packing_freight_fees`:
- 固定費計 `fixed_cost_total`:
- 農機減価償却費 `machinery_depreciation_cost`:
- 機械修理費 `machinery_repair_cost`:
- 施設減価償却費 `facility_depreciation_cost`:
- 施設修理費 `facility_repair_cost`:
- 雇用費 `labor_cost`:
- 土地改良及び水利費 `land_improvement_and_water_cost`:
- 見積額 `estimated_amount`:
- 労賃見積額 `imputed_labor_cost`:
- 地代見積額（田） `imputed_rent_paddy`:
- 地代見積額（畑） `imputed_rent_upland`:
- 地代見積額（樹園） `imputed_rent_orchard`:
- 地代見積額（ハウス） `imputed_rent_greenhouse`:
- 資本利子見積額 `imputed_interest`:
- 生産費（副産物価値控除前） `production_cost_before_subproduct_value_deduction`:

### 資本設備と減価償却費用

この類型で使用する資本設備（土地、機材など）に関する情報となります。
1つの類型で複数の設備を使用することになりますので、`.items` という配列内に、
使用する設備に関する情報を表すJSONオブジェクトをセットしてください。
JSONオブジェクトの定義は以下となります。
すべて任意キー（null許容）で、農業技術文書に記載があれば適当な型で値をセットし、記載が無ければ `null` としてください。

| フィールド名 | 型 | 説明 |
|---|---|---|
| `item_name` | `str` | 資本設備名 |
| `amount` | `int` | 資本設備の数量 |
| `specification` | `str` | 資本設備の仕様・型式・構造・能力を表現したテキスト |
| `acquisition_cost` | `int` | 設備を獲得するのにかかる金額 |
| `service_life` | `int` | 耐用年数・耐久年数 |
| `depreciation_cost` | `int` | 年間の減価償却費用 |

## 経営指標のデータ型

1つの農業技術文書には複数の経営指標（栽培作物の収支、技術仕様）が記述されている可能性があります。
すべて抽出して以下に定義するJSONオブジェクトとして書き出してください。

* `id`: 指標名（なんでもよいです; 評価には直接使用しません）
* `crop_name`: 栽培する作物名
* `balance`: 栽培する作物の収支表
* `work_schedule`: 栽培時間表・スケジュール
* `work_technologies`: 栽培に際し使用する作業技術一覧

経営指標は作物ごとに、収支表 `balance` と作業時間表 `work_schedule` 、作業技術一覧表 `work_technologies` の3つから構成されます。
各項目の定義/スキーマは以下となります。

### 収支表

作物ごとに定めた単位面積あたりでの栽培で見込める収入とその内訳、及び支出とその内訳を表した収支表になります。
収入、支出項目は以下となります。金額はすべて `float` 型としています。
また各収入、支出の項目の後ろに `_unit` とついた `str`型のフィールド名がありますが、これはそれぞれの項目の単位系を表しています。

- 所得 `income`: 
- 粗収益 `gross_revenue`:
- 販売収入 `sales_revenue`:
- 収量（主産物） `amount_of_yielding_main_product`:
- 単価（主産物） `unit_price_main_product`: 
- その他収入（副産物、交付金など） `other_income`: 
- 経営費計 `management_cost_total`:
- 変動費計 `variable_cost_total`:
- 種苗費 `seedling_cost`:
- 肥料費 `fertilizer_cost`:
- 農薬費 `pesticide_cost`:
- 諸材料費 `materials_cost`:
- 動力光熱費 `fuel_and_utilities_cost`:
- 農具費 `farm_tools_cost`:
- 共済費 `insurance_cost`:
- 荷造運賃手数料 `packing_freight_fees`:
- 固定費計 `fixed_cost_total`:
- 農機減価償却費 `machinery_depreciation_cost`:
- 機械修理費 `machinery_repair_cost`:
- 施設減価償却費 `facility_depreciation_cost`:
- 施設修理費 `facility_repair_cost`:
- 雇用費 `labor_cost`:
- 土地改良及び水利費 `land_improvement_and_water_cost`:
- 見積額 `estimated_amount`:
- 労賃見積額 `imputed_labor_cost`:
- 地代見積額（田） `imputed_rent_paddy`:
- 地代見積額（畑） `imputed_rent_upland`:
- 地代見積額（樹園） `imputed_rent_orchard`:
- 地代見積額（ハウス） `imputed_rent_greenhouse`:
- 資本利子見積額 `imputed_interest`:
- 生産費（副産物価値控除前） `production_cost_before_subproduct_value_deduction`:

### 作業時間表

作物の栽培におけるスケジュールになります。
スケジュールは適当な単位で区切られていますので、作業内容と単位期間における作業時間を以下のJSONオブジェクトで表現してください。

* `term_unit`: 各月を上旬・下旬で区切っている場合は `"上下旬"` 、上旬・中旬・下旬で区切っている場合は `"上中下旬"` をセットしてくださいください。
* `items`: 各作業の単位期間における作業時間一覧（以下に定義するJSONオブジェクトの配列となります）

| フィールド名 | 型 | 説明 |
|---|---|---|
| `name` | `str` | 作業名 |
| `period` | `str` | 期間名（※） |
| `hours` | `float` | この期間における作業時間 |

（※）期間名は以下の列挙値のいずれかをとります。

- `1月上旬`
- `1月中旬`
- `1月下旬`
- `2月上旬`
- `2月中旬`
- `2月下旬`
- `3月上旬`
- `3月中旬`
- `3月下旬`
- `4月上旬`
- `4月中旬`
- `4月下旬`
- `5月上旬`
- `5月中旬`
- `5月下旬`
- `6月上旬`
- `6月中旬`
- `6月下旬`
- `7月上旬`
- `7月中旬`
- `7月下旬`
- `8月上旬`
- `8月中旬`
- `8月下旬`
- `9月上旬`
- `9月中旬`
- `9月下旬`
- `10月上旬`
- `10月中旬`
- `10月下旬`
- `11月上旬`
- `11月中旬`
- `11月下旬`
- `12月上旬`
- `12月中旬`
- `12月下旬`

### 作業技術一覧

作物の栽培に必要な技術一覧となります。

* `items`: 以下に定義する栽培に必要な技術を表現したJSONオブジェクトの配列

作業技術のJSONスキーマは以下となります。

| フィールド名 | 型 | 説明 |
|---|---|---|
| `name` | `str` | 作業名 |
| `description` | `str` | 作業の技術内容 |
| `eqiupments` | `list[WorkTechnologyEquipment]` | 以下に定義する作業に必要な機械器具類の一覧 |
| `materials` | `list[WorkTechnologyMaterial]` | 以下に定義する作業に必要な資材類の一覧 |
| `number_of_workers` | `int` | 作業人数 |
| `total_number_of_hours` | `float` | 作業時間 |
| `cost` | `int` | （評価には使用しない項目になりますので適当な値をセットしてください） |
| `note` | `str` | 作業における特記事項・備考 |

機械器具類のJSONスキーマは以下となります。

| フィールド名 | 型 | 説明 |
|---|---|---|
| `name` | `str` | 機械器具類の名称 |
| `hour` | `float` | 想定する使用時間 |

資材類のJSONスキーマは以下となります。

| フィールド名 | 型 | 説明 |
|---|---|---|
| `name` | `str` | 資材名 |
| `usage` | `str` | 使用する資材の数量 |
| `usage_unit` | `str` | 資材の使用量の単位 |
