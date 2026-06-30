#!/usr/bin/env python3
# pip install openai
# vllm serve Qwen/Qwen3-VL-8B-Instruct
# python3 baseline.py -f fit-qa_test_formalrun.jsonl -i png --model Qwen/Qwen3-VL-8B-Instruct --api_key "" --base_url http://localhost:8000/v1 --temperature 0.0 -o prediction_qwen.jsonl
# python3 baseline.py -f fit-qa_test_formalrun.jsonl -i png --model gpt-5.4 -o prediction_gpt.jsonl

import argparse
import base64
import json
from pathlib import Path

import tqdm
from openai import OpenAI
from pydantic import BaseModel, Field

SYSTEM_PROMPT = "あなたはQAアシスタントです。質問に対して、短い語句で簡潔に答えてください。説明は不要です。"


def main():
    parser = argparse.ArgumentParser(
        description="NTCIR-19 DAGRI FiT-QA サブタスクのベースラインシステム")
    parser.add_argument("-f", "--input_file", type=Path,
                        required=True, help="入力データを指定します")
    parser.add_argument("-i", "--image_dir", type=Path,
                        required=True, help="pngディレクトリを指定します"),
    parser.add_argument("-o", "--output_file", type=Path,
                        required=True, help="予測結果の出力先ファイルを指定します"),
    parser.add_argument("--model", required=True, help="OpenAI model")
    parser.add_argument("--api_key", default=None, help="OpenAI api_key")
    parser.add_argument("--base_url", default=None, help="OpenAI base_url")
    parser.add_argument("--temperature", type=float,
                        default=1.0, help="OpenAI temperature")
    parser.add_argument("--max_retries", type=int,
                        default=2, help="OpenAI max_retries")
    args = parser.parse_args()

    client = OpenAI(api_key=args.api_key, base_url=args.base_url,
                    max_retries=args.max_retries)

    with open(args.input_file, "r", encoding="utf-8") as fp:
        data = [json.loads(line) for line in fp]

    outputs = []
    for line in tqdm.tqdm(data):
        with open(args.image_dir / line["file_name"], "rb") as fi:
            img = base64.b64encode(fi.read()).decode("utf-8")

        completion = client.chat.completions.create(
            model=args.model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": [
                    {"type": "image_url", "image_url": {
                        "url": f"data:image/png;base64,{img}"}},
                    {"type": "text", "text": line["question"]},
                ]}
            ],
            reasoning_effort="medium",
            temperature=args.temperature,
            top_p=1.0,
            store=False,
        )
        answer = completion.choices[0].message.content
        outputs.append(
            {"question_id": line["question_id"], "answer": answer, "competion": completion.model_dump()})

    with open(args.output_file, "w", encoding="utf-8") as f:
        for line in outputs:
            print(json.dumps(line, ensure_ascii=False), file=f)


if __name__ == "__main__":
    main()
