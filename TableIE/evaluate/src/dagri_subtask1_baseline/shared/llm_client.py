"""Baseline用LLMクライアント薄ラッパー。

概要:
JSON検証付きのテキスト/マルチモーダル呼び出しを提供し、
抽出器側はプロンプトと出力モデル定義に集中できるようにします。

実装意図:
再試行や検証失敗の扱いを統一し、抽出段階ごとの実装ばらつきを抑えます。
"""

from __future__ import annotations

import json
import os
import base64
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pydantic
from openai import OpenAI


@dataclass
class LLMRuntime:
    client: OpenAI | None
    model: str

    def is_available(self) -> bool:
        return self.client is not None

    def request_json(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        response_model: type[pydantic.BaseModel],
        text_format: dict[str, Any] | None = None,
    ) -> pydantic.BaseModel:
        if self.client is None:
            raise RuntimeError("OpenAI client is unavailable.")

        validation_error: str | None = None
        for _ in range(2):
            input_text = user_prompt
            if validation_error is not None:
                input_text += (
                    "\n\nYour previous output was invalid. "
                    f"Validation error: {validation_error}. "
                    "Return only valid JSON."
                )

            create_kwargs: dict[str, Any] = {
                "model": self.model,
                "input": [
                    {
                        "role": "system",
                        "content": [{"type": "input_text", "text": system_prompt}],
                    },
                    {
                        "role": "user",
                        "content": [{"type": "input_text", "text": input_text}],
                    },
                ],
            }
            if text_format is not None:
                create_kwargs["text"] = {"format": text_format}

            response = self.client.responses.create(**create_kwargs)
            raw_output = (getattr(response, "output_text", None) or "").strip()
            if not raw_output:
                validation_error = "empty response"
                continue

            try:
                payload = json.loads(raw_output)
                return response_model.model_validate(payload)
            except (json.JSONDecodeError, pydantic.ValidationError) as error:
                validation_error = str(error)

        raise RuntimeError(f"LLM extraction failed: {validation_error}")

    def request_json_multimodal(
        self,
        *,
        system_prompt: str,
        page_inputs: list[dict[str, Any]],
        instructions: str,
        response_model: type[pydantic.BaseModel],
        text_format: dict[str, Any] | None = None,
    ) -> pydantic.BaseModel:
        if self.client is None:
            raise RuntimeError("OpenAI client is unavailable.")

        validation_error: str | None = None
        for _ in range(2):
            dynamic_instructions = instructions
            if validation_error is not None:
                dynamic_instructions += (
                    "\n\nYour previous output was invalid. "
                    f"Validation error: {validation_error}. "
                    "Return only valid JSON."
                )

            create_kwargs: dict[str, Any] = {
                "model": self.model,
                "input": [
                    {
                        "role": "system",
                        "content": [{"type": "input_text", "text": system_prompt}],
                    },
                    {
                        "role": "user",
                        "content": _build_multimodal_content(
                            page_inputs=page_inputs,
                            instructions=dynamic_instructions,
                        ),
                    },
                ],
            }
            if text_format is not None:
                create_kwargs["text"] = {"format": text_format}

            response = self.client.responses.create(**create_kwargs)
            raw_output = (getattr(response, "output_text", None) or "").strip()
            if not raw_output:
                validation_error = "empty response"
                continue

            try:
                payload = json.loads(raw_output)
                return response_model.model_validate(payload)
            except (json.JSONDecodeError, pydantic.ValidationError) as error:
                validation_error = str(error)

        raise RuntimeError(f"LLM extraction failed: {validation_error}")


def _build_multimodal_content(
    *,
    page_inputs: list[dict[str, Any]],
    instructions: str,
) -> list[dict[str, Any]]:
    content: list[dict[str, Any]] = [{"type": "input_text", "text": instructions}]

    for page_input in page_inputs:
        page_number = page_input["page_number"]
        text = page_input["text"]
        content.append(
            {
                "type": "input_text",
                "text": f"[page:{page_number}] OCR text:\n{text}",
            }
        )
        image_path = page_input.get("image_path")
        if image_path is None:
            continue
        image_url = _path_to_data_url(Path(image_path))
        content.append(
            {
                "type": "input_image",
                "image_url": image_url,
            }
        )
    return content


def _path_to_data_url(path: Path) -> str:
    data = path.read_bytes()
    encoded = base64.b64encode(data).decode("ascii")
    return f"data:image/png;base64,{encoded}"


def build_json_schema_format(
    *,
    name: str,
    response_model: type[pydantic.BaseModel],
    strict: bool = True,
) -> dict[str, Any]:
    schema = response_model.model_json_schema()
    normalized_schema = _normalize_schema_for_openai(schema)
    return {
        "type": "json_schema",
        "name": name,
        "schema": normalized_schema,
        "strict": strict,
    }


def _normalize_schema_for_openai(schema: dict[str, Any]) -> dict[str, Any]:
    def _walk(node: Any) -> Any:
        if isinstance(node, dict):
            updated = {key: _walk(value) for key, value in node.items()}
            if updated.get("type") == "object":
                if "additionalProperties" not in updated:
                    updated["additionalProperties"] = False
                properties = updated.get("properties")
                if isinstance(properties, dict):
                    updated["required"] = list(properties.keys())
            return updated
        if isinstance(node, list):
            return [_walk(value) for value in node]
        return node

    return _walk(schema)


def create_llm_runtime_from_env() -> LLMRuntime:
    try:
        from openai import OpenAI
    except ModuleNotFoundError:
        return LLMRuntime(client=None, model=_get_model())

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return LLMRuntime(client=None, model=_get_model())

    return LLMRuntime(client=OpenAI(api_key=api_key), model=_get_model())


def _get_model() -> str:
    return os.getenv("BASELINE_OPENAI_MODEL", "gpt-5-mini")
