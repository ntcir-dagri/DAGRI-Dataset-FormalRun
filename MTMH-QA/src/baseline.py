from __future__ import annotations

"""OpenAI互換のChat Completions APIでMTMH-QAの回答欄を埋めるスクリプト。

各質問とprefA/prefB配下のJSONファイル群をLLMへ渡し、構造化JSONとして回答を
受け取ってJSONLへ保存します。途中で止まっても再開できるよう、既存の出力
ファイルに入っている回答は再利用します。
"""

# ---------------------------------------------------------------------------
# Baseline overview
# ---------------------------------------------------------------------------
# このスクリプトは MTMH-QA Subtask 2 の回答生成ベースラインです。
#
# 処理の流れ:
#   1. 評価用JSONLから question / id を読み込む
#   2. input_prefA / input_prefB 以下の農業経営JSONを読み込む
#   3. 質問に関係しそうなJSONだけを抽出してLLMへ渡す
#   4. LLMから {"answers": [{"id": ..., "answer": ...}]} 形式で回答を受け取る
#   5. 各行の answer を埋めたJSONLをバッチごとに保存する
#
# 公開用サンプルとして、実運用で起きがちなAPIエラーにもある程度対応します。
# 例: 429/502のリトライ、タイムアウト、reasoning_effort非対応、
#     json_schema非対応、バッチ回答で一部IDが欠けるケースなど。
# ---------------------------------------------------------------------------

import argparse
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime
from pathlib import Path
from typing import Any


DEFAULT_MODEL = "gpt-5.4-mini"
DEFAULT_INPUT = Path("dryrun_train_eval/dryrun_eval_renumbered_clean_answer.jsonl")
DEFAULT_OUTPUT = Path("dryrun_train_eval/dryrun_eval_renumbered_filled_answers.jsonl")
DEFAULT_PROMPT = Path("prompts/fill_answers_prompt_ja.md")

# 既定値は「高精度を狙いすぎる」よりも「まず最後まで完走しやすい」側に
# 寄せています。精度を上げたい場合は、実行時に --reasoning low や
# --batch-size の調整を試してください。
DEFAULT_BATCH_SIZE = 5
DEFAULT_SLEEP_SECONDS = 10.0
DEFAULT_REASONING_EFFORT = "none"
DEFAULT_TIMEOUT_SECONDS = 900.0
DEFAULT_CONTEXT_MODE = "filtered"
DEFAULT_MAX_CONTEXT_FILES = 18
DEFAULT_MAX_COMPLETION_TOKENS = 2048
DEFAULT_RETRIES = 5


JsonValue = Any


class IncompleteCompletionError(RuntimeError):
    """モデル出力が max_completion_tokens に達して途中で切れたことを表します。

    reasoning を有効にすると、見える回答を出す前に reasoning tokens だけで
    上限を使い切ることがあります。その場合は通常のJSONパースエラーではなく、
    この例外として扱い、後段で上限増加や reasoning 無効化のフォールバックを
    行います。
    """
    pass


def parse_args() -> argparse.Namespace:
    """コマンドライン引数を定義します。

    ベースラインとしては引数なしで動くことを重視しつつ、実験しやすいように
    モデル、reasoning、バッチサイズ、タイムアウト、コンテキスト抽出方式などを
    すべてCLIから上書きできるようにしています。
    """
    parser = argparse.ArgumentParser(
        description="OpenAI APIを呼び出してMTMH-QAのJSONL回答欄を埋めます。"
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=Path(__file__).resolve().parent,
        help="MTMH-QAディレクトリ。既定値はこのスクリプトがあるディレクトリです。",
    )
    parser.add_argument(
        "--input",
        type=Path,
        default=DEFAULT_INPUT,
        help="入力JSONL。相対パスの場合は--rootからの相対パスとして扱います。",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT,
        help="出力JSONL。相対パスの場合は--rootからの相対パスとして扱います。",
    )
    parser.add_argument(
        "--prompt",
        type=Path,
        default=DEFAULT_PROMPT,
        help="プロンプトファイル。相対パスの場合は--rootからの相対パスとして扱います。",
    )
    parser.add_argument(
        "--model",
        default=DEFAULT_MODEL,
        help=f"OpenAIのモデル名。既定値は{DEFAULT_MODEL}です。",
    )
    parser.add_argument(
        "--reasoning",
        choices=("none", "minimal", "low", "medium", "high", "xhigh"),
        default=DEFAULT_REASONING_EFFORT,
        help=(
            "Chat Completions APIへ渡すreasoning_effort。"
            f"既定値は{DEFAULT_REASONING_EFFORT}です。"
        ),
    )
    parser.add_argument(
        "--api-key-env",
        default="OPENAI_API_KEY",
        help="OpenAI APIキーを格納した環境変数名。",
    )
    parser.add_argument(
        "--base-url",
        default=os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1"),
        help="OpenAI互換APIのベースURL。既定値はOPENAI_BASE_URLまたはOpenAI公式URLです。",
    )
    parser.add_argument(
        "--max-rows",
        type=int,
        default=None,
        help="処理する行数の上限。少数行のテスト実行に使います。",
    )
    parser.add_argument(
        "--start-id",
        type=int,
        default=None,
        help="この値以上のidを持つ行だけを処理します。",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="出力ファイルに既存回答があっても再生成します。",
    )
    parser.add_argument(
        "--sleep",
        type=float,
        default=DEFAULT_SLEEP_SECONDS,
        help=f"API呼び出し間に待機する秒数。既定値は{DEFAULT_SLEEP_SECONDS}秒です。",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=DEFAULT_BATCH_SIZE,
        help=f"1回のAPI呼び出しでまとめて回答させる質問数。既定値は{DEFAULT_BATCH_SIZE}です。",
    )
    parser.add_argument(
        "--retries",
        type=int,
        default=DEFAULT_RETRIES,
        help=f"一時的なAPIエラーに対するリトライ回数。既定値は{DEFAULT_RETRIES}です。",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=DEFAULT_TIMEOUT_SECONDS,
        help=f"1回のAPI呼び出しでレスポンスを待つ秒数。既定値は{DEFAULT_TIMEOUT_SECONDS}秒です。",
    )
    parser.add_argument(
        "--max-completion-tokens",
        type=int,
        default=DEFAULT_MAX_COMPLETION_TOKENS,
        help=(
            "生成トークン数の上限。reasoning tokensも含みます。"
            f"既定値は{DEFAULT_MAX_COMPLETION_TOKENS}です。"
        ),
    )
    parser.add_argument(
        "--response-format",
        choices=("json_schema", "json_object"),
        default="json_schema",
        help="OpenAIのresponse_format。json_schema非対応時はjson_objectへフォールバックします。",
    )
    parser.add_argument(
        "--context-mode",
        choices=("filtered", "full"),
        default=DEFAULT_CONTEXT_MODE,
        help="LLMへ渡す入力JSONを質問ごとに絞るか、常に全件渡すかを指定します。",
    )
    parser.add_argument(
        "--max-context-files",
        type=int,
        default=DEFAULT_MAX_CONTEXT_FILES,
        help=f"filtered時に追加選択する関連ファイル数の上限。既定値は{DEFAULT_MAX_CONTEXT_FILES}です。",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="API呼び出し、リトライ、待機の進捗ログを標準エラーに出力します。",
    )
    return parser.parse_args()


def log_verbose(enabled: bool, message: str) -> None:
    """--verbose 指定時だけ、時刻付きログを標準エラーへ出します。

    APIの待機時間が長い場合、標準出力だけでは「止まっている」のか
    「API応答待ち」なのか分かりにくいため、詳細ログは stderr に分けています。
    """
    if enabled:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] {message}", file=sys.stderr, flush=True)


def sleep_with_log(seconds: float, verbose: bool, reason: str) -> None:
    """待機理由をログに残してから sleep します。"""
    if seconds <= 0:
        return
    log_verbose(verbose, f"sleeping {seconds:.1f}s: {reason}")
    time.sleep(seconds)


def resolve_under_root(root: Path, path: Path) -> Path:
    """相対パスを MTMH-QA ディレクトリ配下のパスへ解決します。"""
    return path if path.is_absolute() else root / path


def read_jsonl(path: Path) -> list[dict[str, JsonValue]]:
    """JSONLファイルを読み込みます。

    このタスクでは1行が1問に対応するJSONオブジェクトです。空行は無視し、
    JSONとして壊れている行や、オブジェクト以外の行があれば早めに例外にします。
    """
    rows: list[dict[str, JsonValue]] = []
    with path.open("r", encoding="utf-8") as file:
        for line_number, line in enumerate(file, start=1):
            stripped = line.strip()
            if not stripped:
                continue
            try:
                row = json.loads(stripped)
            except json.JSONDecodeError as exc:
                raise ValueError(f"Invalid JSON at {path}:{line_number}") from exc
            if not isinstance(row, dict):
                raise ValueError(f"Each JSONL row must be an object: {path}:{line_number}")
            rows.append(row)
    return rows


def write_jsonl(path: Path, rows: list[dict[str, JsonValue]]) -> None:
    """JSONLファイルを書き出します。

    直接出力先へ書き込むと、実行中断時にファイルが壊れる可能性があります。
    そのため一時ファイルへ全行を書き出してから `replace` で差し替えます。
    """
    # 保存中に中断しても出力ファイルが壊れにくいよう、一時ファイル経由で書き込みます。
    path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = path.with_suffix(path.suffix + ".tmp")
    with temp_path.open("w", encoding="utf-8", newline="\n") as file:
        for row in rows:
            file.write(json.dumps(row, ensure_ascii=False, separators=(",", ":")) + "\n")
    temp_path.replace(path)


def load_previous_answers(path: Path) -> dict[int, JsonValue]:
    """既存の出力JSONLから回答済みの id -> answer を読み取ります。

    長時間のAPI実行では途中で止まることがあるため、再実行時に回答済みの行を
    スキップできるようにしています。`--overwrite` 指定時はこの結果を使いません。
    """
    # --overwriteがない場合、既存の回答を読み込んで途中再開に使います。
    if not path.exists():
        return {}
    answers: dict[int, JsonValue] = {}
    for row in read_jsonl(path):
        record_id = row.get("id")
        if isinstance(record_id, int) and row.get("answer") not in ("", None):
            answers[record_id] = row["answer"]
    return answers


def load_data_context(root: Path) -> dict[str, JsonValue]:
    """input_prefA / input_prefB 以下のJSONをすべて読み込みます。

    戻り値の `files` には、`input_prefA/management_indicators/.../balance.json`
    のような相対パスをキーとしてJSON内容を格納します。LLMに相対パスも渡すことで、
    自治体、作目、経営モデル、ファイル種別を区別しやすくしています。
    """
    # LLMが自治体・作目・経営モデルの出典を区別できるよう、相対パス付きで渡します。
    context: dict[str, JsonValue] = {
        "municipality_aliases": {
            "自治体A": "prefA",
            "自治体B": "prefB",
            "input_prefA": "prefA",
            "input_prefB": "prefB",
        },
        "files": {},
    }
    files = context["files"]
    assert isinstance(files, dict)

    for input_dir_name in ("input_prefA", "input_prefB"):
        input_dir = root / input_dir_name
        if not input_dir.exists():
            raise FileNotFoundError(f"Missing data directory: {input_dir}")
        for json_path in sorted(input_dir.rglob("*.json")):
            relative_path = json_path.relative_to(root).as_posix()
            with json_path.open("r", encoding="utf-8") as file:
                try:
                    files[relative_path] = json.load(file)
                except json.JSONDecodeError as exc:
                    raise ValueError(f"Invalid JSON data file: {json_path}") from exc
    return context


def context_files(data_context: dict[str, JsonValue]) -> dict[str, JsonValue]:
    """data_context から files オブジェクトを安全に取り出します。"""
    files = data_context.get("files")
    if not isinstance(files, dict):
        raise ValueError("data_context must contain a files object")
    return files


def detect_input_dirs(question_rows: list[dict[str, JsonValue]]) -> set[str]:
    """質問文から参照すべき自治体ディレクトリを推定します。

    質問文には `自治体A/B` のほか、文字化けした自治体名が含まれることがあります。
    どちらも検出できない場合は安全側に倒し、A/B両方を候補にします。
    """
    combined = "\n".join(str(row.get("question", "")) for row in question_rows)
    input_dirs: set[str] = set()
    if "自治体A" in combined or "閾ｪ豐ｻ菴鄭" in combined or "input_prefA" in combined:
        input_dirs.add("input_prefA")
    if "自治体B" in combined or "閾ｪ豐ｻ菴釘" in combined or "input_prefB" in combined:
        input_dirs.add("input_prefB")
    return input_dirs or {"input_prefA", "input_prefB"}


def file_relevance_score(path: str, data: JsonValue, question_text: str) -> int:
    """質問文とJSONファイルの関連度を簡易スコアリングします。

    本格的なRAGではなく、ベースライン向けの軽量なヒューリスティックです。
    ファイルパスに含まれる作目名や、JSON内の文字列値が質問文に含まれる場合に
    関連度を高くします。
    """
    # JSON文字列中の値やファイルパスが質問文に現れる場合、そのファイルを優先します。
    path_parts = [part for part in path.replace("\\", "/").split("/") if part]
    score = 0
    matched = False
    for part in path_parts:
        if len(part) >= 2 and part in question_text:
            score += 50 + len(part)
            matched = True

    text = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
    quoted_strings = set(re.findall(r'"([^"]{2,})"', text))
    for value in quoted_strings:
        if value in question_text:
            score += 20 + min(len(value), 20)
            matched = True

    # work_scheduleやbalanceなど、質問種別が不明でも比較的参照頻度が高い表を少し優先します。
    if matched and path.endswith("/balance.json"):
        score += 3
    if matched and path.endswith("/work_schedule.json"):
        score += 2
    if matched and path.endswith("/work_technologies.json"):
        score += 1
    return score


def filtered_data_context(
    data_context: dict[str, JsonValue],
    question_rows: list[dict[str, JsonValue]],
    max_context_files: int,
    verbose: bool,
) -> dict[str, JsonValue]:
    """質問バッチに関係しそうなJSONだけを抽出します。

    全JSONを毎回LLMへ渡すと入力が大きくなり、タイムアウトやreasoning tokensの
    肥大化が起きやすくなります。そこで既定では、自治体を絞ったうえで、
    質問文に現れる作目名・項目名にマッチするファイルを優先して渡します。
    """
    all_files = context_files(data_context)
    input_dirs = detect_input_dirs(question_rows)
    question_text = "\n".join(str(row.get("question", "")) for row in question_rows)

    selected: dict[str, JsonValue] = {}

    # 自治体が分かる場合は、その自治体の経営モデル表を基礎情報として必ず含めます。
    for path, data in all_files.items():
        if not isinstance(path, str):
            continue
        if not any(path.startswith(input_dir + "/") for input_dir in input_dirs):
            continue
        if "/management_types/" in path:
            selected[path] = data

    scored: list[tuple[int, str, JsonValue]] = []
    for path, data in all_files.items():
        if not isinstance(path, str):
            continue
        if path in selected:
            continue
        if not any(path.startswith(input_dir + "/") for input_dir in input_dirs):
            continue
        score = file_relevance_score(path, data, question_text)
        if score > 0:
            scored.append((score, path, data))

    scored.sort(key=lambda item: (-item[0], item[1]))
    for _, path, data in scored[:max_context_files]:
        selected[path] = data

    # 名称照合に失敗した場合でも、その自治体のファイルを少量は渡して完全な空振りを避けます。
    if len(selected) == 0:
        for path, data in all_files.items():
            if isinstance(path, str) and any(path.startswith(input_dir + "/") for input_dir in input_dirs):
                selected[path] = data
                if len(selected) >= max_context_files:
                    break

    log_verbose(
        verbose,
        (
            f"filtered context dirs={sorted(input_dirs)} files={len(selected)}/"
            f"{len(all_files)}"
        ),
    )
    return {
        "municipality_aliases": data_context.get("municipality_aliases", {}),
        "files": dict(sorted(selected.items())),
    }


def data_context_for_batch(
    data_context: dict[str, JsonValue],
    question_rows: list[dict[str, JsonValue]],
    context_mode: str,
    max_context_files: int,
    verbose: bool,
) -> dict[str, JsonValue]:
    """バッチに渡すコンテキストを作ります。

    `full` は全JSONを渡します。`filtered` は質問に関係しそうなファイルだけを
    渡します。公開ベースラインでは速度・安定性のため `filtered` を既定にしています。
    """
    if context_mode == "full":
        return data_context
    return filtered_data_context(data_context, question_rows, max_context_files, verbose)


def answer_value_schema() -> dict[str, JsonValue]:
    """`answer` に許可するJSON値のスキーマを返します。

    評価データの answer は、単一回答なら文字列、複数回答ならリスト、
    項目名付き回答ならオブジェクトになります。ここではその3種類を許可します。
    """
    # 評価形式に合わせ、answerの値は文字列・リスト・オブジェクトのいずれも許可します。
    return {
        "anyOf": [
            {"type": "string"},
            {
                "type": "array",
                "items": {
                    "anyOf": [
                        {"type": "string"},
                        {"type": "number"},
                        {"type": "boolean"},
                        {"type": "null"},
                        {"type": "array", "items": {}},
                        {"type": "object", "additionalProperties": True},
                    ]
                },
            },
            {"type": "object", "additionalProperties": True},
        ]
    }


def answer_schema_response_format() -> dict[str, JsonValue]:
    """Chat Completions APIへ渡す JSON Schema response_format を作ります。

    バッチ処理では、モデルに `{"answers": [{"id": ..., "answer": ...}]}`
    という形で返させます。idを含めることで、モデルが順序を変えても対応できます。
    """
    return {
        "type": "json_schema",
        "json_schema": {
            "name": "mtmh_qa_answer_batch",
            "strict": False,
            "schema": {
                "type": "object",
                "properties": {
                    "answers": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "id": {"type": "integer"},
                                "answer": answer_value_schema(),
                            },
                            "required": ["id", "answer"],
                            "additionalProperties": False,
                        },
                    }
                },
                "required": ["answers"],
                "additionalProperties": False,
            },
        },
    }


def make_request_body(
    model: str,
    reasoning_effort: str,
    max_completion_tokens: int | None,
    prompt: str,
    question_rows: list[dict[str, JsonValue]],
    data_context: dict[str, JsonValue],
    response_format: str,
) -> dict[str, JsonValue]:
    """Chat Completions API のリクエストボディを作ります。

    system message にはプロンプトファイルの内容を入れ、user message には
    質問バッチと参照JSONをまとめたJSON文字列を入れます。

    `reasoning_effort` は `none` の場合は送信しません。モデルやOpenAI互換APIに
    よって未対応の場合があるため、不要なパラメータは送らない方針です。
    """
    # 指示文はプロンプトファイル、質問と大きな入力データはユーザーメッセージに入れます。
    user_content = {
        "questions": [
            {"id": row.get("id"), "question": row.get("question", "")}
            for row in question_rows
        ],
        "data_context": data_context,
    }
    body: dict[str, JsonValue] = {
        "model": model,
        "messages": [
            {"role": "system", "content": prompt},
            {
                "role": "user",
                "content": json.dumps(user_content, ensure_ascii=False, separators=(",", ":")),
            },
        ],
    }
    if reasoning_effort != "none":
        body["reasoning_effort"] = reasoning_effort
    if max_completion_tokens is not None and max_completion_tokens > 0:
        body["max_completion_tokens"] = max_completion_tokens
    if response_format == "json_schema":
        body["response_format"] = answer_schema_response_format()
    else:
        body["response_format"] = {"type": "json_object"}
    return body


def retry_sleep_seconds(
    error_body: str,
    attempt: int,
    status_code: int | None = None,
    retry_after: str | None = None,
) -> float:
    """リトライ前に待機する秒数を決めます。

    429などで `Retry-After` ヘッダーや "try again in ..." が返る場合はそれを優先し、
    502/503/504などのゲートウェイ系エラーは少し長めに待ちます。
    """
    if retry_after:
        try:
            return min(max(float(retry_after), 1.0), 120.0)
        except ValueError:
            pass
    match = re.search(r"try again in ([0-9.]+)(ms|s)", error_body, flags=re.IGNORECASE)
    if match:
        value = float(match.group(1))
        seconds = value / 1000 if match.group(2).lower() == "ms" else value
        return min(max(seconds + 0.5, 1.0), 60.0)
    base = 5 if status_code in {502, 503, 504} else 1
    return min(base * (2**attempt), 120.0)


def is_reasoning_parameter_error(error: RuntimeError) -> bool:
    """reasoning_effort 非対応らしいエラーかを判定します。"""
    message = str(error).lower()
    return (
        "reasoning_effort" in message
        or "reasoning" in message
        or "unsupported parameter" in message
        or "unrecognized request argument" in message
    )


def is_timeout_error(error: RuntimeError) -> bool:
    """タイムアウト由来のエラーかを判定します。"""
    return "timed out" in str(error).lower()


def larger_completion_limit(max_completion_tokens: int | None) -> int | None:
    """出力上限に達したときの再試行用に、少し大きい上限値を返します。"""
    if max_completion_tokens is None or max_completion_tokens <= 0:
        return None
    return min(max(max_completion_tokens * 4, 4096), 8192)


def post_chat_completion(
    base_url: str,
    api_key: str,
    body: dict[str, JsonValue],
    retries: int,
    timeout: float,
    verbose: bool,
) -> dict[str, JsonValue]:
    """Chat Completions APIへPOSTします。

    依存関係を増やさないため、OpenAI Python SDKではなく標準ライブラリの
    `urllib` を使っています。HTTP 429/5xx、URLエラー、タイムアウトは
    指定回数までリトライします。
    """
    # OpenAI Python SDKを必須にしないため、標準ライブラリでHTTP送信します。
    url = base_url.rstrip("/") + "/chat/completions"
    payload = json.dumps(body, ensure_ascii=False).encode("utf-8")
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    for attempt in range(retries + 1):
        request = urllib.request.Request(url, data=payload, headers=headers, method="POST")
        log_verbose(
            verbose,
            (
                f"request attempt {attempt + 1}/{retries + 1}: "
                f"model={body.get('model')} "
                f"reasoning_effort={body.get('reasoning_effort', 'none')} "
                f"max_completion_tokens={body.get('max_completion_tokens', 'unset')} "
                f"timeout={timeout}s payload_bytes={len(payload)}"
            ),
        )
        started_at = time.monotonic()
        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:
                response_bytes = response.read()
                elapsed = time.monotonic() - started_at
                log_verbose(
                    verbose,
                    f"response received in {elapsed:.1f}s bytes={len(response_bytes)}",
                )
                response_json = json.loads(response_bytes.decode("utf-8"))
                if verbose:
                    usage = response_json.get("usage")
                    choices = response_json.get("choices")
                    finish_reason = None
                    if isinstance(choices, list) and choices:
                        first_choice = choices[0]
                        if isinstance(first_choice, dict):
                            finish_reason = first_choice.get("finish_reason")
                    log_verbose(
                        verbose,
                        f"finish_reason={finish_reason} usage={json.dumps(usage, ensure_ascii=False)}",
                    )
                return response_json
        except urllib.error.HTTPError as exc:
            elapsed = time.monotonic() - started_at
            error_body = exc.read().decode("utf-8", errors="replace")
            log_verbose(
                verbose,
                f"HTTPError {exc.code} after {elapsed:.1f}s: {error_body[:500]}",
            )
            if exc.code in {408, 409, 429, 500, 502, 503, 504} and attempt < retries:
                sleep_with_log(
                    retry_sleep_seconds(
                        error_body,
                        attempt,
                        status_code=exc.code,
                        retry_after=exc.headers.get("Retry-After"),
                    ),
                    verbose,
                    f"retry after HTTP {exc.code}",
                )
                continue
            raise RuntimeError(f"OpenAI API HTTP {exc.code}: {error_body}") from exc
        except urllib.error.URLError as exc:
            elapsed = time.monotonic() - started_at
            log_verbose(verbose, f"URLError after {elapsed:.1f}s: {exc}")
            if attempt < retries:
                sleep_with_log(min(2**attempt, 60), verbose, "retry after URL error")
                continue
            raise RuntimeError(f"OpenAI API request failed: {exc}") from exc
        except TimeoutError as exc:
            elapsed = time.monotonic() - started_at
            log_verbose(verbose, f"TimeoutError after {elapsed:.1f}s")
            if attempt < retries:
                sleep_with_log(min(2**attempt, 60), verbose, "retry after timeout")
                continue
            raise RuntimeError(
                f"OpenAI API request timed out after {timeout} seconds"
            ) from exc

    raise RuntimeError("OpenAI API request failed after retries")


def parse_batch_answers(api_response: dict[str, JsonValue]) -> dict[int, JsonValue]:
    """APIレスポンスから `id -> answer` を取り出します。

    `finish_reason=length` は、max_completion_tokensに達してJSONが途中で
    切れている可能性が高いため、専用例外として扱います。
    """
    try:
        choice = api_response["choices"][0]
        content = choice["message"]["content"]
    except (KeyError, IndexError, TypeError) as exc:
        raise ValueError(f"Unexpected API response shape: {api_response}") from exc
    if isinstance(choice, dict) and choice.get("finish_reason") == "length":
        usage = api_response.get("usage")
        raise IncompleteCompletionError(
            f"Model stopped because max_completion_tokens was reached. usage={usage}"
        )
    if not isinstance(content, str):
        raise ValueError(f"Expected message content to be a string: {content!r}")
    try:
        parsed = json.loads(content)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Model did not return valid JSON: {content}") from exc

    if isinstance(parsed, dict) and isinstance(parsed.get("answers"), list):
        answer_items = parsed["answers"]
    elif isinstance(parsed, list):
        answer_items = parsed
    else:
        raise ValueError(f'Model response must contain an "answers" list: {content}')

    answers: dict[int, JsonValue] = {}
    for item in answer_items:
        if not isinstance(item, dict):
            raise ValueError(f"Each batch answer must be an object: {content}")
        record_id = item.get("id")
        if not isinstance(record_id, int) or "answer" not in item:
            raise ValueError(f'Each batch answer needs integer "id" and "answer": {content}')
        answers[record_id] = item["answer"]
    return answers


def call_model_for_answers(
    *,
    base_url: str,
    api_key: str,
    model: str,
    reasoning_effort: str,
    max_completion_tokens: int | None,
    prompt: str,
    question_rows: list[dict[str, JsonValue]],
    data_context: dict[str, JsonValue],
    response_format: str,
    retries: int,
    timeout: float,
    verbose: bool,
) -> dict[int, JsonValue]:
    """1バッチ分の質問をモデルへ投げ、回答辞書を返します。

    ここでは実運用で起きやすい失敗をフォールバックします。
    - 出力上限到達: reasoningなし、または大きい上限で再試行
    - reasoning_effort非対応: reasoningなしで再試行
    - タイムアウト: reasoningなしで再試行
    - json_schema非対応: json_objectで再試行
    """
    body = make_request_body(
        model,
        reasoning_effort,
        max_completion_tokens,
        prompt,
        question_rows,
        data_context,
        response_format,
    )
    try:
        response = post_chat_completion(base_url, api_key, body, retries, timeout, verbose)
        return parse_batch_answers(response)
    except IncompleteCompletionError as exc:
        next_limit = larger_completion_limit(max_completion_tokens)
        if reasoning_effort != "none":
            log_verbose(
                verbose,
                (
                    "completion limit was exhausted before visible JSON was produced; "
                    "retrying once without reasoning_effort"
                ),
            )
            retry_body = make_request_body(
                model,
                "none",
                next_limit,
                prompt,
                question_rows,
                data_context,
                response_format,
            )
            response = post_chat_completion(
                base_url,
                api_key,
                retry_body,
                retries,
                timeout,
                verbose,
            )
            return parse_batch_answers(response)
        if next_limit is not None and next_limit != max_completion_tokens:
            log_verbose(
                verbose,
                f"completion limit was exhausted; retrying with max_completion_tokens={next_limit}",
            )
            retry_body = make_request_body(
                model,
                reasoning_effort,
                next_limit,
                prompt,
                question_rows,
                data_context,
                response_format,
            )
            response = post_chat_completion(
                base_url,
                api_key,
                retry_body,
                retries,
                timeout,
                verbose,
            )
            return parse_batch_answers(response)
        raise exc
    except RuntimeError as exc:
        if reasoning_effort != "none" and is_reasoning_parameter_error(exc):
            log_verbose(
                verbose,
                "reasoning_effort was rejected; retrying once without reasoning_effort",
            )
            retry_body = make_request_body(
                model,
                "none",
                max_completion_tokens,
                prompt,
                question_rows,
                data_context,
                response_format,
            )
            response = post_chat_completion(
                base_url,
                api_key,
                retry_body,
                retries,
                timeout,
                verbose,
            )
            return parse_batch_answers(response)
        if reasoning_effort != "none" and is_timeout_error(exc):
            log_verbose(
                verbose,
                "request timed out with reasoning_effort; retrying once without reasoning_effort",
            )
            retry_body = make_request_body(
                model,
                "none",
                max_completion_tokens,
                prompt,
                question_rows,
                data_context,
                response_format,
            )
            response = post_chat_completion(
                base_url,
                api_key,
                retry_body,
                retries,
                timeout,
                verbose,
            )
            return parse_batch_answers(response)
        # OpenAI互換APIの中にはjson_schemaではなくjson_objectだけ対応するものがあります。
        if response_format == "json_schema" and "response_format" in str(exc):
            log_verbose(verbose, "json_schema was rejected; retrying with json_object")
            fallback_body = make_request_body(
                model,
                reasoning_effort,
                max_completion_tokens,
                prompt,
                question_rows,
                data_context,
                "json_object",
            )
            response = post_chat_completion(
                base_url,
                api_key,
                fallback_body,
                retries,
                timeout,
                verbose,
            )
            return parse_batch_answers(response)
        raise


def main() -> int:
    """メイン処理です。

    大まかな流れ:
    1. 入力JSONL、プロンプト、参照JSONを読み込む
    2. 既存出力があれば回答済み行を復元する
    3. 未回答行だけをバッチ化する
    4. バッチごとにコンテキストを作ってAPIへ投げる
    5. バッチごとに出力JSONLを保存する
    """
    args = parse_args()
    root = args.root.resolve()
    input_path = resolve_under_root(root, args.input)
    output_path = resolve_under_root(root, args.output)
    prompt_path = resolve_under_root(root, args.prompt)

    api_key = os.environ.get(args.api_key_env)
    if not api_key:
        print(f"Environment variable {args.api_key_env} is not set.", file=sys.stderr)
        return 2
    if args.batch_size < 1:
        print("--batch-size must be greater than or equal to 1.", file=sys.stderr)
        return 2
    if args.max_context_files < 1:
        print("--max-context-files must be greater than or equal to 1.", file=sys.stderr)
        return 2

    prompt = prompt_path.read_text(encoding="utf-8")
    data_context = load_data_context(root)
    rows = read_jsonl(input_path)

    # 処理前に、出力ファイルへ保存済みの回答を今回の入力行へコピーします。
    # これにより、途中で止まった場合でも再実行時に続きから処理できます。
    previous_answers = {} if args.overwrite else load_previous_answers(output_path)
    for row in rows:
        record_id = row.get("id")
        if isinstance(record_id, int) and record_id in previous_answers:
            row["answer"] = previous_answers[record_id]

    write_jsonl(output_path, rows)

    # 今回APIへ投げる対象行だけを抽出します。
    # 既にanswerが入っている行は、--overwrite がない限りスキップします。
    pending_rows: list[dict[str, JsonValue]] = []
    for row in rows:
        record_id = row.get("id")
        if args.max_rows is not None and len(pending_rows) >= args.max_rows:
            break
        if args.start_id is not None and isinstance(record_id, int) and record_id < args.start_id:
            continue
        if not args.overwrite and row.get("answer") not in ("", None):
            continue
        pending_rows.append(row)

    log_verbose(
        args.verbose,
        (
            f"loaded rows={len(rows)} pending={len(pending_rows)} "
            f"batch_size={args.batch_size} retries={args.retries} timeout={args.timeout} "
            f"context_mode={args.context_mode} max_context_files={args.max_context_files}"
        ),
    )

    for start in range(0, len(pending_rows), args.batch_size):
        batch_rows = pending_rows[start : start + args.batch_size]
        batch_ids = [row.get("id") for row in batch_rows]
        print(
            f"[{start + 1}-{start + len(batch_rows)}/{len(pending_rows)}] "
            f"answering ids={batch_ids}",
            flush=True,
        )
        # filteredモードでは、質問ごとに関連ファイルだけを抽出します。
        # fullモードでは、全JSONをそのまま渡します。
        batch_context = data_context_for_batch(
            data_context,
            batch_rows,
            args.context_mode,
            args.max_context_files,
            args.verbose,
        )
        answers_by_id = call_model_for_answers(
            base_url=args.base_url,
            api_key=api_key,
            model=args.model,
            reasoning_effort=args.reasoning,
            max_completion_tokens=args.max_completion_tokens,
            prompt=prompt,
            question_rows=batch_rows,
            data_context=batch_context,
            response_format=args.response_format,
            retries=args.retries,
            timeout=args.timeout,
            verbose=args.verbose,
        )
        for row in batch_rows:
            record_id = row.get("id")
            if not isinstance(record_id, int):
                raise ValueError(f'Question row has invalid "id": {row}')
            if record_id not in answers_by_id:
                # バッチ回答では、まれに一部idだけ返ってこないことがあります。
                # その場合はバッチ全体を失敗扱いにせず、欠けた質問だけ単問で再試行します。
                log_verbose(
                    args.verbose,
                    f"model response missed id={record_id}; retrying this question alone",
                )
                single_context = data_context_for_batch(
                    data_context,
                    [row],
                    args.context_mode,
                    args.max_context_files,
                    args.verbose,
                )
                single_answers = call_model_for_answers(
                    base_url=args.base_url,
                    api_key=api_key,
                    model=args.model,
                    reasoning_effort=args.reasoning,
                    max_completion_tokens=args.max_completion_tokens,
                    prompt=prompt,
                    question_rows=[row],
                    data_context=single_context,
                    response_format=args.response_format,
                    retries=args.retries,
                    timeout=args.timeout,
                    verbose=args.verbose,
                )
                if record_id not in single_answers:
                    raise ValueError(f"Model response did not include answer for id={record_id}")
                answers_by_id[record_id] = single_answers[record_id]
            row["answer"] = answers_by_id[record_id]

        # バッチごとに保存しておくことで、長時間実行中の失敗時にも進捗を失いにくくします。
        write_jsonl(output_path, rows)
        log_verbose(args.verbose, f"saved answers for ids={batch_ids}")
        sleep_with_log(args.sleep, args.verbose, "between batches")

    print(f"Done. Wrote {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
