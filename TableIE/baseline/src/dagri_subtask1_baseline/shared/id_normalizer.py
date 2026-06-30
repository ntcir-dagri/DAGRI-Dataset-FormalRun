"""識別子正規化ユーティリティ。

概要:
抽出した名称から提出用の安定IDを生成するための共通処理を提供します。

実装意図:
baselineの抽出ロジックで使うID規則を一箇所に集約し、
類型名・作目名で同じ正規化ルールを適用できるようにします。
"""

from __future__ import annotations

import hashlib
import re
import unicodedata


_NON_ALNUM_PATTERN = re.compile(r"[^a-z0-9]+")


def normalize_identifier(value: str) -> str:
    normalized = unicodedata.normalize("NFKC", value).lower().strip()
    normalized = _NON_ALNUM_PATTERN.sub("-", normalized)
    normalized = normalized.strip("-")
    if normalized:
        return normalized

    digest = hashlib.sha1(value.encode("utf-8")).hexdigest()[:8]
    return f"item-{digest}"


def uniquify_identifiers(values: list[str]) -> list[str]:
    seen: dict[str, int] = {}
    result: list[str] = []
    for value in values:
        if value not in seen:
            seen[value] = 1
            result.append(value)
            continue

        seen[value] += 1
        result.append(f"{value}-{seen[value]}")
    return result
