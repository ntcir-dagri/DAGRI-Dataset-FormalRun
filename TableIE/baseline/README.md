# SDK for DAGRI Subtask 1: Table IE 

農業技術文書から情報抽出・構造化を行うタスクである
DAGRI Subtask 1: Table IE の参加者向けの開発キットです。

`dagri_subtask1_sdk` パッケージでは、主に以下の機能をサポートしています。

- 抽出・構造化する経営類型、経営指標のデータ構造定義とデータクラスの提供
- 提出ファイルの作成と検証

データクラスの定義説明については [DATA_SCHEMA.md](./docs/DATA_SCHEMA.md) に詳細を記載しています。
提出ファイルは、抽出/構造化した経営類型、経営指標をJSONLの形式に書き出します。
sdkで提供するデータクラス及び書き出しのユーティリティを使用しますと、JSONの型、形式の不正を防ぎやすいです。
また提出ファイルの形式に問題がないかのバリデータも同梱しています。提出前にファイル形式などの確認に活用ください。詳細は [SUBMISSION.md](./docs/SUBMISSION.md) を参照ください。

また、`dagri_subtask1_baseline` パッケージにて、ベースラインプログラムを同梱しています。
ベースラインプログラムの実装方針については [BASELINE_PIPELINE.md](./docs/BASELINE_PIPELINE.md) に詳細を記載しています。


## セットアップ

pythonのバージョン、パッケージ管理ツールである `uv` の使用を前提とします。

```bash
uv sync --all-packages --all-groups
```

またpdftotextコマンドの実行ができる環境が必要です。

```bash
apt install xpdf
```

さらにベースラインプログラムはOpenAI APIを使用しています。
ベースラインプログラムを実行する場合は以下の環境変数を定義してください。

```bash
export OPENAI_API_KEY="OpenAI APIのアクセスキー"
```

## INDEX

* データクラス定義・抽出構造化項目: [DATA_SCHEMA.md](./docs/DATA_SCHEMA.md)
* 提出ファイルの作成・バリデーション: [SUBMISSION.md](./docs/SUBMISSION.md)
* ベースラインプログラム: [BASELINE_PIPELINE.md](./docs/BASELINE_PIPELINE.md)
