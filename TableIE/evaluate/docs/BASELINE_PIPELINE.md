# Baseline Pipeline Guide

本資料は、コンペティション参加者向けに baseline 処理の流れと改善ポイントを説明するドキュメントです。  
対象コードは主に `baseline.py` と `src/dagri_subtask1_baseline/` 配下です。

## 1. 目的

baseline は、農業技術文書 PDF から以下を抽出し、提出 JSONL（1 PDF = 1 行）を生成します。

- `management_types`
- `management_indicators`

設計方針は次の通りです。

- ページ探索はテキスト中心、詳細抽出は画像+テキストを活用
- 失敗しても可能な限り継続し、提出ファイル生成を止めない

## 2. 実行方法と入出力

ベースライン処理では、OpenAI APIを使用します。事前に以下の環境変数を定義して下さい。

```bash
export OPENAI_API_KEY="OpenAI APIのアクセスキー"
```

実行コマンド例:

```bash
uv run python baseline.py -d ../DAGRI-Dataset-DryRun/TableIE -s submission-baseline.jsonl --log-level INFO
```

CLI 引数:

- `--data-dir, -d`: データセットディレクトリ
- `--submission, -s`: 提出 JSONL の出力先
- `--log-level`: `DEBUG / INFO / WARNING / ERROR`

### 2.1 依存コマンドとインストール手順

baseline では、PDF のテキスト抽出とページ画像化のために外部コマンドを利用します。

- 必須: `pdftotext`
利用箇所: `src/dagri_subtask1_baseline/shared/pdf_text_extractor.py`
- 画像化で利用: `pdftoppm` または `pdftocairo`（どちらか）
利用箇所: `src/dagri_subtask1_baseline/shared/pdf_images.py`
実装では `pdftoppm` を優先し、見つからない場合は `pdftocairo` を自動利用

インストール手順:

- macOS（Homebrew）

```bash
brew install poppler
```

- Ubuntu

```bash
sudo apt update
sudo apt install -y poppler-utils
```

実行前チェック:

```bash
pdftotext -v
pdftoppm -v
pdftocairo -v
```

入力探索規則:

- `{{data_dir}}/{{prefecture_name}}/{{file_id}}.pdf`

sdkにて、データセットディレクトリ以下の都道府県、PDFファイルの探索を行います。

出力:

- `SubmissionDataset` を JSONL として書き出し
- 1 ドキュメントにつき 1 行（`prefecture_name`, `id`, `management_types`, `management_indicators`）

## 3. 全体パイプライン

`baseline.py` の `run_baseline(...)` は、各 PDF に対して次を実行します。

1. PDF パス探索  
`FileSystemAgriculturalTechnicalPDFDocumentDiscoveryService` で対象 PDF を列挙します。
2. テキスト抽出  
`shared/pdf_text_extractor.py` の `extract_text_from_pdf` で本文を取得します。
3. ページ構築（画像+テキスト）  
`shared/pdf_pages.py` の `build_pdf_pages` で `PDFPage(number, text, image_path)` を作成します。
4. 経営類型抽出  
`management_type.pipeline.extract_management_types(...)` を呼びます。
5. 経営指標抽出  
`management_indicator.pipeline.extract_management_indicators(...)` を呼びます。
6. 提出行の組み立て・書き出し  
`Submission` を蓄積し、最後に JSONL を出力します。

## 4. Management Type 抽出手順

`src/dagri_subtask1_baseline/management_type/` で、項目別にページ探索、情報抽出について実装しています。

1. `name/extractor.py`  
経営類型名を抽出し、`ManagementType` を初期化します。
2. `premise/page_finder.py` と `premise/extractor.py`  
前提情報ページを探索し、`premise` を反映します。
3. `growing_area/page_finder.py` と `growing_area/extractor.py`  
作目と規模情報を抽出して `growing_area` を反映します。
4. `balance/page_finder.py` と `balance/extractor.py`  
類型全体の収支を抽出して `balance` を反映します。
5. `capital_equipment/page_finder.py` と `capital_equipment/extractor.py`  
資本設備一覧を抽出して `capital_equipment` を反映します。

`pipeline.py` は上記を順に呼ぶオーケストレーターです。  
ページ未検出時は警告ログを出して初期値を維持します。

## 5. Management Indicator 抽出手順

`src/dagri_subtask1_baseline/management_indicator/` で、作目ごとに段階抽出します。

1. 作目起点の初期化  
`management_types[].growing_area.items[].crop_name` を収集し、`ManagementIndicator` を初期化します。
2. `balance/page_finder.py` と `balance/extractor.py`  
品目別収支ページを探索し、`balance` を反映します。
3. `work_technologies/page_finder.py` と `work_technologies/extractor.py`  
作業・技術情報を抽出して `work_technologies` を反映します。
4. `work_schedule/page_finder.py` と `work_schedule/extractor.py`  
栽培スケジュール（ガント含む）を抽出して `work_schedule` を反映します。

`term_unit` はページ内容から判定し、未判定時は既定値で継続します。

## 6. LLM 呼び出しと出力安定化

`shared/llm_client.py` が LLM 呼び出しをまとめて扱います。

- テキスト専用: `request_json(...)`
- マルチモーダル: `request_json_multimodal(...)`
- `text.format` に JSON Schema を指定して構造化出力を強制
- Pydantic 検証失敗時は 1 回再試行
- スキーマは OpenAI strict 要件に合わせて正規化

これにより、抽出モジュール側は「プロンプト定義」と「結果マッピング」に集中できます。

## 7. 失敗時の挙動

baseline は「止めない」ことを優先します。

- PDF 読み込み失敗: その PDF は空配列を入れて継続
- ページ画像生成失敗: テキストのみページにフォールバックして継続
- 各抽出ステップ失敗: 該当項目は初期値維持で継続
- 最終的に、処理可能だった全 PDF 分の JSONL を出力

## 8. 参加者向け改善ポイント

着手しやすい改善ポイントは次の通りです。

1. page finder の改善  
キーワード一致以外の方法で探索する等、探索精度を上げると後段抽出の品質が上がります。
2. extractor プロンプトの改善  
表・ガントの読み取り条件、除外条件、単位扱いを明示すると安定します。
3. 後処理ルールの改善  
ID 正規化、重複統合、数値正規化、単位補正を強化できます。
4. 失敗時リカバリの改善  
再試行条件やフォールバック基準を見直すことで頑健性を高められます。

baseline はあくまで最小構成です。  

- パイプラインを土台に、探索・抽出・正規化など各ステップの改善を自由に行ってください。
- このパイプラインが絶対ではありません。探索と抽出を統合する、適当なメトリクスを導入して自己改善を含める、など自由に改善を行ってください。

また、配布するデータセットには、都道府県ごとに抽出のガイドライン `Instructions.md` を同梱しています。
こちらの情報を参考にして処理手続きやロジック、プロンプトを自由に改善してください。
