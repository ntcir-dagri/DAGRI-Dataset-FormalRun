#!/usr/bin/env python3
# pip install mecab-python3 unidic-lite sacrebleu openai socksio

import argparse
import json
import os
import statistics
import traceback
from pathlib import Path

import MeCab
import unidic_lite
import sacrebleu
import tqdm
from openai import OpenAI, DefaultHttpxClient
from pydantic import BaseModel, Field


GS_FILENAME = "fit-qa_gold_formalrun.jsonl"


class EvaluationException(Exception):
    pass


# JSONの読み込み
def load_json(file_path):
    data, questions = {}, {}
    with open(file_path, "r", encoding="utf-8-sig") as f:
        for idx, line in enumerate(f, start=1):
            if not line:
                continue
            try:
                line = json.loads(line)
            except ValueError:
                raise EvaluationException(f"JSON行のデコードに失敗しました: {idx}行目")
            if "question_id" not in line:
                raise EvaluationException(f"question_idが含まれていません: {idx}行目")
            if "answer" not in line:
                raise EvaluationException(f"answerが含まれていません: {idx}行目")
            if type(line["question_id"]) != str:
                raise EvaluationException(
                    f"question_idの型がstringではありません: {idx}行目")
            if type(line["answer"]) != str:
                raise EvaluationException(f"answerの型がstringではありません: {idx}行目")
            if line["question_id"] in data:
                raise EvaluationException(f"question_idが重複しています: {idx}行目")
            data[line["question_id"]] = line["answer"]
            if "question" in line and type(line["question"]) == str:
                questions[line["question_id"]] = line["question"]
    return data, questions


# データの確認
def check_data(eval_data, gold_data, questions):
    for k in gold_data.keys():
        if k not in eval_data.keys():
            raise EvaluationException(f"入力データに回答が含まれていません: question_id={k}")
        if k not in questions.keys():
            raise EvaluationException(
                f"内部エラー（Gold Standardにquestionが含まれていません）: question_id={k}")
    for k in eval_data.keys():
        if k not in gold_data.keys():
            raise EvaluationException(
                f"不明なquestion_idが含まれています: question_id={k}")


# スコアの算出
def calculate_bleu(eval_data, gold_data):
    tagger = MeCab.Tagger(
        f'-Owakati -d "{unidic_lite.DICDIR}" -r "{os.path.join(unidic_lite.DICDIR, "mecabrc")}"')

    hypotheses, references = [], []
    for question_id, gold_value in tqdm.tqdm(gold_data.items(), desc="BLEU"):
        gold_parsed = tagger.parse(gold_value)
        eval_parsed = tagger.parse(eval_data[question_id])
        references.append(
            " ".join(gold_parsed.strip().split() if gold_parsed else ""))
        hypotheses.append(
            " ".join(eval_parsed.strip().split() if eval_parsed else ""))

    bleu = sacrebleu.corpus_bleu(hypotheses=hypotheses, references=[
                                 references], tokenize="none")
    return float(bleu.score), bleu.__dict__


class Result(BaseModel):
    score: int = Field(ge=1, le=5)


def calculate_llm_judge(eval_data, gold_data, questions, model, api_key, base_url, max_retries, proxy):
    SYSTEM_PROMPT = (
        "You are an expert evaluator.\n"
        "Evaluate how well the Prediction matches the Answer for the Question.\n\n"
        "Scoring rubric:\n"
        "5: Fully correct and complete.\n"
        "4: Mostly correct with minor errors.\n"
        "3: Partially correct.\n"
        "2: Mostly incorrect.\n"
        "1: Completely incorrect or irrelevant.\n"
    )
    USER_PROMPT_TEMPLATE = (
        "Question: {Question}\n"
        "Answer: {Answer}\n"
        "Prediction: {Prediction}\n"
    )
    client = OpenAI(api_key=api_key, base_url=base_url, max_retries=max_retries,
                    http_client=DefaultHttpxClient(proxy=proxy if proxy else None),
                    timeout=20)

    scores, results, errors = [], {}, 0
    for question_id, gold_value in tqdm.tqdm(gold_data.items(), desc="LLM-as-a-Judge"):
        completion = client.chat.completions.parse(
            model=model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": USER_PROMPT_TEMPLATE.format(
                    Question=questions[question_id],
                    Answer=gold_value,
                    Prediction=eval_data[question_id],
                )}
            ],
            reasoning_effort="low",
            temperature=0.0,
            top_p=1.0,
            response_format=Result,
            store=False,
        )
        score = completion.choices[0].message.parsed.score
        if type(score) != int or score < 1 or 5 < score:
            score = 3
            errors += 1
        scores.append(score)
        results[question_id] = completion.model_dump()

    mean_score = statistics.mean(scores)
    return mean_score, {"completions": results, "errors": errors}


def main():
    # デフォルトのGSデータのファイルパス
    gs_data = (Path(__file__).parents[0] / GS_FILENAME)
    parser = argparse.ArgumentParser(
        description="NTCIR-19 DAGRI FiT-QA サブタスクの評価スクリプト")
    parser.add_argument("-f", "--input_file",
                        required=True, help="入力データを指定します")
    parser.add_argument("-g", "--gs_data", required=(not gs_data.exists()),
                        default=gs_data, help="Gold Standard データを指定します")
    parser.add_argument("--model", default="openai/gpt-oss-120b", help="OpenAI model")
    parser.add_argument("--api_key", default=None, help="OpenAI api_key")
    parser.add_argument("--base_url", default=None, help="OpenAI base_url")
    parser.add_argument("--max_retries", type=int,
                        default=2, help="OpenAI max_retries")
    parser.add_argument("--proxy", default=None, help="HTTP proxy")
    args = parser.parse_args()

    # データ読み込み
    eval_data, _ = load_json(args.input_file)
    gold_data, questions = load_json(args.gs_data)

    check_data(eval_data, gold_data, questions)
    bleu_score, bleu_results = calculate_bleu(eval_data, gold_data)
    llm_judge_score, llm_judge_results = calculate_llm_judge(
        eval_data, gold_data, questions, args.model, args.api_key, args.base_url, args.max_retries, args.proxy)

    return json.dumps({
        "status": "success",
        "scores": [
            bleu_score,
            llm_judge_score,
        ],
        "bleu_results": bleu_results,
        "llm_judge_results": llm_judge_results,
    }, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    try:
        print(main())
    except EvaluationException as e:
        print(json.dumps(
            {"status": "failed", "message": e.args[0]}, ensure_ascii=False, indent=2))
        traceback.print_exc()
    except Exception:
        print(json.dumps({"status": "failed"}, ensure_ascii=False, indent=2))
        traceback.print_exc()
