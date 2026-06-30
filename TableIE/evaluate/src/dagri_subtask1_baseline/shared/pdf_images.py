"""PDFページ画像のレンダリングユーティリティ。

概要:
PDFをページ単位のPNGへ変換し、表やガントチャートの視覚情報をLLMへ渡せる形にします。

実装意図:
環境依存を抑えるため、pdftoppm/pdftocairoのどちらかを自動選択します。
"""

from __future__ import annotations

from pathlib import Path
import shutil
import subprocess


def render_pdf_to_images(
    pdf_path: str | Path,
    output_dir: str | Path,
    *,
    dpi: int = 150,
) -> list[Path]:
    pdf = Path(pdf_path)
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    prefix = out_dir / "page"

    if shutil.which("pdftoppm"):
        command = [
            "pdftoppm",
            "-png",
            "-r",
            str(dpi),
            str(pdf),
            str(prefix),
        ]
    elif shutil.which("pdftocairo"):
        command = [
            "pdftocairo",
            "-png",
            "-r",
            str(dpi),
            str(pdf),
            str(prefix),
        ]
    else:
        raise RuntimeError("pdftoppm or pdftocairo command is required.")

    completed = subprocess.run(
        command,
        check=False,
        capture_output=True,
        text=True,
    )
    if completed.returncode != 0:
        stderr = completed.stderr.strip() or "failed to render pdf images"
        raise RuntimeError(stderr)

    return sorted(out_dir.glob("page-*.png"))
