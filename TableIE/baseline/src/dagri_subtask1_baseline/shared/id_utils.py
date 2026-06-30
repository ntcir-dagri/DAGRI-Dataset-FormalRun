"""識別子の正規化ユーティリティ。

概要:
作目名や類型名から提出用IDを安定生成するための関数を公開します。

実装意図:
ID生成ルールを一箇所に寄せ、抽出器ごとの差分や不整合を防ぎます。
"""

from dagri_subtask1_baseline.shared.id_normalizer import (
    normalize_identifier,
    uniquify_identifiers,
)

__all__ = ["normalize_identifier", "uniquify_identifiers"]
