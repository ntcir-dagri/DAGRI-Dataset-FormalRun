# dagri-subtask1-eval

DAGRI Subtask 1 リーダーボード評価スクリプト

## セットアップ

パッケージ管理ツール `uv` が必要になります。
pythonのバージョンは 3.13 以上を前提とし、

```bash
$ uv python pin <3.13以上>
$ uv sync --all-packages
```

## 使い方

### コマンドラインツールとして使用する場合

`-m dagri_subtask1_eval.main` でスクリプトとして実行することができます。

```bash
$ uv run python -m dagri_subtask1_eval.main --help

usage: dagri-subtask1-eval [-h] submission_file eval_file

Evaluate a submission file against a ground-truth dataset.

positional arguments:
  submission_file  Path to the submission JSONL file.
  eval_file        Path to the evaluation JSONL file.

options:
  -h, --help       show this help message and exit
```

コマンドライン引数として、

* 第1引数: 参加者が提出したファイル（JSONL）
* 第2引数: 評価用ファイル（JSONL）

### パッケージとしてimportする場合

参加者の提出ファイルと評価用ファイルを比較し評価値を算出する、というユースケースを `dagri_subtask1_eval` パッケージで実装しています。
評価の手続きは `dagri_subtask1_eval.usecase.evaluate_usecase` の `EvaluateUsecase` に実装しています。
データの読み込み方や各項目の評価戦略を差し替えられるような実装となっていますが、
標準のセットアップは `dagri_subtask1_eval.main.container` の `build_evaluate_usecase` で取得できます。

```python
>>> from dagri_subtask1_eval.main.container import build_evaluate_usecase
>>> usecase = build_evaluate_usecase()
```

このユースケースの `execute` 関数をコールすると評価を行います。
第1引数に参加者提出ファイル（JSONL）、第2引数に評価用データファイル（JSONL）をとり、評価値を返します。

```python
>>> submission_file_path: str = "/path/to/submission.jsonl
>>> eval_file_path: str = "/path/to/evaluation.jsonl
>>> eval_result = usecase.execute(submission_file_path, eval_file_path)
```

## 評価スクリプトの挙動について

### 配列要素（management_types / management_indicators）が未対応の場合

`management_types` / `management_indicators` の要素が正解データ側と対応付けられない場合、
未対応要素は 1 件の 0 点として扱うのではなく、その要素で本来評価される内部フィールド数に相当する件数の 0 点として加算されます。
これにより、要素を提出しない場合が、要素を提出して内部フィールドを誤った場合より過大に有利になりにくくなります。
また、`growing_area`、`capital_equipment`、`work_schedule`、`work_technologies` の内部配列要素も、類似度が一定以上の場合にのみ対応付けられます。

### 内部配列アライメントの閾値設定

内部配列のアライメントに使う類似度閾値は、以下の環境変数で個別に調整できます。未設定の場合はすべて `0.6` が使われます。

* `DAGRI_GROWING_AREA_MIN_SIMILARITY`
* `DAGRI_CAPITAL_EQUIPMENT_MIN_SIMILARITY`
* `DAGRI_WORK_SCHEDULE_MIN_SIMILARITY`
* `DAGRI_WORK_TECHNOLOGY_MIN_ITEM_SIMILARITY`
* `DAGRI_WORK_TECHNOLOGY_MIN_EQUIPMENT_SIMILARITY`
* `DAGRI_WORK_TECHNOLOGY_MIN_MATERIAL_SIMILARITY`

設定値は `0.0` から `1.0` の範囲の小数を想定しています。

### 提出用ファイルに不備があった場合の挙動

#### JSONL型に不正があった場合

提出用ファイルは JSONL として 1 行ずつ読み込まれ、各行を `Submission` スキーマで検証します。空行は無視されます。

提出用ファイルに必須項目の欠落や型不一致などの不備がある場合は、
不正な行を見つけた時点では中断せず、ファイル全体を読み終えたあとに
`DatasetValidationError` を送出します。
エラーメッセージには、各不備について少なくとも次の情報が含まれます。

* 行番号
* 不備があった項目パス
* 検証エラーメッセージ

エラーメッセージの例:

```text
データセットに不正な値があります: line=1 path=management_types message=Input should be a valid array, line=1 path=management_indicators message=Input should be a valid array, line=2 path=id message=Field required
```


#### 提出データ中のサンプル数と評価データ中のサンプル数が一致しない場合

提出用ファイルと評価用ファイルに含まれるサンプルの組
`(prefecture_name, id)` が一致しない場合は、評価処理の開始前に `ValueError` を送出します。
このとき、不足または余分だったサンプルキーの一覧がエラーメッセージに含まれます。

エラーメッセージの例:

```text
提出データセットと正解データセットに含まれるサンプルが一致していません: [('tokyo', '1'), ('tokyo', '2')]
```
