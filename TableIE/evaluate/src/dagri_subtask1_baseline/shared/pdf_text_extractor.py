"""PDFテキスト抽出ユーティリティ。

概要:
`pdftotext` コマンドを利用してPDF本文を文字列として取得します。

実装意図:
テキスト抽出方式はbaselineの実装選択に依存するため、
SDKではなくbaseline側のsharedユーティリティとして管理します。
"""

from pathlib import Path
import subprocess


def extract_text_from_pdf(pdf_path: str | Path) -> str:
    """Extract text from PDF with pdftotext command."""
    path = Path(pdf_path)
    completed = subprocess.run(
        ["pdftotext", "-layout", str(path), "-"],
        check=False,
        capture_output=True,
        text=True,
    )
    if completed.returncode != 0:
        error_message = completed.stderr.strip() or "pdftotext command failed."
        raise RuntimeError(error_message)
    return completed.stdout
