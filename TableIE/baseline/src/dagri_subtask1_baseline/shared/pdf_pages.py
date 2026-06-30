"""PDFページ表現（テキスト+画像）を扱うユーティリティ。

概要:
ページ番号・OCRテキスト・画像パスをまとめた`PDFPage`を構築し、
探索・抽出処理へ同じデータ構造を渡せるようにします。

実装意図:
探索はテキスト、抽出は画像+テキストという方針を崩さず、
呼び出し側のインターフェースを単純に保ちます。
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .pdf_images import render_pdf_to_images


@dataclass(frozen=True)
class PDFPage:
    number: int
    text: str
    image_path: Path | None = None


def split_text_into_pages(pdf_text: str) -> list[PDFPage]:
    chunks = pdf_text.split("\f")
    return [PDFPage(number=index + 1, text=chunk) for index, chunk in enumerate(chunks)]


def build_pdf_pages(
    *,
    pdf_path: str | Path,
    pdf_text: str,
    image_dir: str | Path,
    dpi: int = 150,
) -> list[PDFPage]:
    pages = split_text_into_pages(pdf_text)
    images = render_pdf_to_images(pdf_path=pdf_path, output_dir=image_dir, dpi=dpi)

    result: list[PDFPage] = []
    for index, page in enumerate(pages):
        image_path = images[index] if index < len(images) else None
        result.append(
            PDFPage(
                number=page.number,
                text=page.text,
                image_path=image_path,
            )
        )

    return result


def select_pages(pages: list[PDFPage], page_numbers: list[int]) -> list[PDFPage]:
    by_number = {page.number: page for page in pages}
    return [by_number[number] for number in page_numbers if number in by_number]
