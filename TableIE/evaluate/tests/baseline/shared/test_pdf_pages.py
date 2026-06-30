from pathlib import Path

from dagri_subtask1_baseline.shared import pdf_pages


def test_build_pdf_pages_aligns_text_and_images(monkeypatch, tmp_path):
    def _render_stub(**_kwargs):
        p1 = tmp_path / "page-1.png"
        p2 = tmp_path / "page-2.png"
        p1.write_bytes(b"png")
        p2.write_bytes(b"png")
        return [p1, p2]

    monkeypatch.setattr(pdf_pages, "render_pdf_to_images", _render_stub)

    pages = pdf_pages.build_pdf_pages(
        pdf_path=Path("/tmp/sample.pdf"),
        pdf_text="a\fb",
        image_dir=tmp_path,
    )

    assert len(pages) == 2
    assert pages[0].number == 1
    assert pages[0].text == "a"
    assert pages[0].image_path == tmp_path / "page-1.png"
    assert pages[1].image_path == tmp_path / "page-2.png"
