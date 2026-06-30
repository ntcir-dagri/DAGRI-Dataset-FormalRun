from pathlib import Path

from dagri_subtask1_baseline.shared import pdf_images


class _Completed:
    def __init__(self, returncode: int, stderr: str = ""):
        self.returncode = returncode
        self.stderr = stderr


def test_render_pdf_to_images_uses_pdftoppm(monkeypatch, tmp_path):
    calls = {}

    def _which_stub(name: str):
        if name == "pdftoppm":
            return "/usr/bin/pdftoppm"
        return None

    def _run_stub(command, check, capture_output, text):
        calls["command"] = command
        (tmp_path / "page-1.png").write_bytes(b"png")
        return _Completed(returncode=0)

    monkeypatch.setattr(pdf_images.shutil, "which", _which_stub)
    monkeypatch.setattr(pdf_images.subprocess, "run", _run_stub)

    actual = pdf_images.render_pdf_to_images(
        pdf_path=tmp_path / "a.pdf",
        output_dir=tmp_path,
    )

    assert calls["command"][0] == "pdftoppm"
    assert len(actual) == 1


def test_render_pdf_to_images_raises_when_command_fails(monkeypatch, tmp_path):
    monkeypatch.setattr(pdf_images.shutil, "which", lambda name: "/usr/bin/pdftoppm")
    monkeypatch.setattr(
        pdf_images.subprocess,
        "run",
        lambda *args, **kwargs: _Completed(returncode=1, stderr="failed"),
    )

    try:
        pdf_images.render_pdf_to_images(pdf_path=tmp_path / "a.pdf", output_dir=tmp_path)
        assert False, "expected RuntimeError"
    except RuntimeError as error:
        assert "failed" in str(error)
