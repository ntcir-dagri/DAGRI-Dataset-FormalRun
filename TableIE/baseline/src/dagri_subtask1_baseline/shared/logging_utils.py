"""ベースライン実行時のログ出力ユーティリティ。

概要:
抽出失敗やページ未検出など、継続可能な問題をlogging経由で統一出力します。

実装意図:
エラー停止ではなくフォールバック継続を採るため、
利用者が後で原因を追跡しやすいログ形式を維持します。
"""

import logging


LOGGER_NAME = "dagri_subtask1_baseline"
logger = logging.getLogger(LOGGER_NAME)


def warn(message: str) -> None:
    logger.warning(message)


def debug(message: str) -> None:
    logger.debug(message)
