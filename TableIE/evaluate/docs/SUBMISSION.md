# Submission Guide

このドキュメントは、提出オブジェクト (`Submission`) と提出ファイルの書き出し・検証処理に関するガイドです。

## 1. 目的と対象

対象は次の3点です。

- 提出データモデル: `src/dagri_subtask1_sdk/domain/submission.py`
- 提出ファイル書き出し: `SubmissionDatasetWriterService` （インターフェース） と `JsonlSubmissionDatasetWriterService` （実装）
- 提出ファイル検証: `SubmissionDiagnoseService` （インターフェース） と `FileSystemSubmissionDiagnoseService` （実装）

## 2. 提出オブジェクトの構造

`Submission` は提出ファイルの1行に対応するオブジェクトです。  
`SubmissionDataset` は提出全体（全行）を `items` 配列で表します。

```python
class Submission(BaseModel):
    prefecture_name: str
    id: str
    management_types: list[ManagementType]
    management_indicators: list[ManagementIndicator]

class SubmissionDataset(BaseModel):
    items: list[Submission]
```

ポイント:

- 提出 JSONL は **1行 = 1農業技術文書（PDF）から抽出した経営類型、経営指標 **
- `SubmissionDataset.items` が提出全行集合
- `prefecture_name` と `id` が、データセット上のPDFを識別するキーとして使われます

## 3. 書き出し処理

書き出しは次の流れです。

1. `CreateSubmissionFileUsecase.execute(...)` を呼ぶ
2. 内部で `SubmissionDatasetWriterService.write(...)` を実行
3. 既定実装 `JsonlSubmissionDatasetWriterService` が JSONL をファイル出力

`JsonlSubmissionDatasetWriterService` の現在の挙動:

- 出力先親ディレクトリがなければ自動作成
- UTF-8 で書き込み
- `SubmissionDataset.items` の各要素を1行ずつ JSON 文字列で出力

## 4. 検証処理

検証は CLI から実行できます。

```bash
python -m dagri_subtask1_sdk.main.diagnose -s submission.jsonl -d /path/to/dataset
```

呼び出し関係:

1. `dagri_subtask1_sdk.main.diagnose` (CLI)
2. `DiagnoseSubmissionUsecase.execute(...)`
3. `SubmissionDiagnoseService.diagnose(...)`
4. 既定実装 `FileSystemSubmissionDiagnoseService`

`FileSystemSubmissionDiagnoseService` の現在の検証項目:

1. 提出ファイルの存在確認
2. JSONL 各行が `Submission` として妥当か（Pydantic検証）
3. データセット内の期待キーとの突合
 - 期待キーは `subtask1_data_dir/test` 配下の `*.pdf` から `(prefecture_name, file_id)` を収集
 - 提出側の `(prefecture_name, id)` と比較して、不足・余分を判定

結果:

- 問題なし: `is_valid=True`、CLIは `OK` を出力し終了コード `0`
- 問題あり: `is_valid=False`、エラーメッセージ一覧を出力し終了コード `1`

## 5. エラーメッセージの例

実装上、次のようなエラーが返ります（文言は実装依存）。

- 提出ファイルが存在しない
 - `提出ファイルが見つかりません: ...`
- JSON形式が不正、または必須フィールド欠落
 - `N行目のJSONが不正です: field=... message=...`
- 提出対象の過不足
 - `提出に不足しているサンプルがあります: [...]`
 - `提出に余分なサンプルがあります: [...]`

## 6. Public APIs / Interfaces

提出関連で参加者が把握すべきインターフェース:

- `Submission`, `SubmissionDataset`
- `SubmissionDatasetWriterService.write(...)`
- `SubmissionDiagnoseService.diagnose(...)`
- `CreateSubmissionFileUsecase`
- `DiagnoseSubmissionUsecase`

CLI:

- `python -m dagri_subtask1_sdk.main.diagnose -s ... -d ...`

## 7. 最小 JSONL 例

以下は1行分の最小例です（実際の提出では対象PDFすべて分の行が必要）。

```json
{"prefecture_name":"tokyo","id":"a","management_types":[],"management_indicators":[]}
```

## 8. 実装上の注意

- baseline は抽出失敗時に、該当PDFを空配列（`management_types=[]`, `management_indicators=[]`）でフォールバックして継続する設計です。
- よくある失敗は次の2つです。
 - `id` 欠落や型不一致による JSON 検証エラー
 - `(prefecture_name, id)` の不一致による不足・余分エラー
- まずは `diagnose` CLI を実行して、提出の構造とキー一致を確認する運用が推奨です。
