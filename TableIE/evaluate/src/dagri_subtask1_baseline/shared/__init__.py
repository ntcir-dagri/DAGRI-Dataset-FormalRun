"""Baselineで共通利用する軽量ユーティリティ群。

概要:
PDFページ構築、LLM呼び出し、ID正規化など項目非依存の処理を集約します。

実装意図:
ドメインロジックはmanagement_type/management_indicator側へ残し、
再利用価値の高い処理だけをここに置きます。
"""
