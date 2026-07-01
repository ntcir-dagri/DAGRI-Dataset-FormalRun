# MTMH-QA Evaluation Script

MTMH-QA 用の評価スクリプトです。評価データ JSONL と参加者提出 JSONL を読み込み、`id` が一致する各オブジェクトの `answer` を比較して精度を計算します。

## 評価ルール

- `id` が一致するレコード同士を比較します。
- `answer` は完全一致で評価します。
- `answer` がリストの場合は順不同で比較します。
- `answer` がオブジェクトの場合は、キー集合が完全一致し、各値が再帰的に一致する必要があります。
- 評価データに存在して提出データに存在しない `id` は不正解扱いになります。
- 提出データにだけ存在する `id` は `unexpected_ids` として返します。

## ファイル構成

- `mtmh_qa_eval/scoring.py`
  - 評価ロジック本体です。
- `mtmh_qa_eval/__main__.py`
  - `python -m mtmh_qa_eval` 用の CLI 入口です。
- `MTMH-QA/evaluate_submission.py`
  - ワークスペース内から実行しやすい薄いラッパーです。

## CLI での使い方

ワークスペースのルートで次を実行します。

```bash
python -m mtmh_qa_eval --gold MTMH-QA\dryrun_train_eval\gold.jsonl --pred MTMH-QA\dryrun_train_eval\submission.jsonl
```

または次でも同じです。

```bash
python MTMH-QA\evaluate_submission.py --gold MTMH-QA\dryrun_train_eval\gold.jsonl --pred MTMH-QA\dryrun_train_eval\submission.jsonl
```

JSON の整形幅を変えたい場合は `--indent` を指定できます。

```bash
python -m mtmh_qa_eval --gold gold.jsonl --pred submission.jsonl --indent 0
```

## 出力形式

出力は JSON です。

```json
{
  "accuracy": 1.0,
  "correct": 107,
  "total": 107,
  "missing_ids": [],
  "unexpected_ids": [],
  "mismatched_ids": []
}
```

- `accuracy`: `correct / total`
- `correct`: 正解した件数
- `total`: 評価データ件数
- `missing_ids`: 評価データにあるが提出データにない `id`
- `unexpected_ids`: 提出データにあるが評価データにない `id`
- `mismatched_ids`: `id` は存在するが `answer` が一致しなかった `id`

## Python モジュールとしての使い方

```python
from mtmh_qa_eval import evaluate_submission

result = evaluate_submission("gold.jsonl", "submission.jsonl")
print(result.accuracy)
print(result.to_dict())
```

個別の `answer` 同士を比較したい場合は `score_answers` も使えます。

```python
from mtmh_qa_eval import score_answers

print(score_answers(["a", "b"], ["b", "a"]))  # True
print(score_answers({"x": ["a", "b"]}, {"x": ["b", "a"]}))  # True
```
