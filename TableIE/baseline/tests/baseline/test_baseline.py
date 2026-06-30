import importlib.util
import json
import logging
from pathlib import Path
import sys

from dagri_subtask1_baseline.shared.pdf_pages import PDFPage
from dagri_subtask1_sdk.domain.management_indicator import ManagementIndicator
from dagri_subtask1_sdk.domain.management_indicators.balance import Balance as IndicatorBalance
from dagri_subtask1_sdk.domain.management_indicators.work_schedule import WorkScheduleList
from dagri_subtask1_sdk.domain.management_indicators.work_technologies import WorkTechnologyList
from dagri_subtask1_sdk.domain.management_type import ManagementType
from dagri_subtask1_sdk.domain.management_types.balance import Balance
from dagri_subtask1_sdk.domain.management_types.capital_equipment import CapitalEquipmentList
from dagri_subtask1_sdk.domain.management_types.growing_area import GrowingAreaList
from dagri_subtask1_sdk.domain.management_types.premise import Premise


def _find_repo_root(start: Path) -> Path:
    for candidate in [start, *start.parents]:
        if (candidate / "baseline.py").exists():
            return candidate
    raise RuntimeError("Could not find repository root that contains baseline.py")


_REPO_ROOT = _find_repo_root(Path(__file__).resolve())
_BASELINE_PATH = _REPO_ROOT / "baseline.py"
_SPEC = importlib.util.spec_from_file_location("baseline", _BASELINE_PATH)
assert _SPEC is not None
assert _SPEC.loader is not None
baseline = importlib.util.module_from_spec(_SPEC)
sys.modules["baseline"] = baseline
_SPEC.loader.exec_module(baseline)


def test_build_submission_sets_values():
    context = baseline.ExtractorContext(
        prefecture_name="tokyo",
        file_id="a",
        pdf_path=Path("/tmp/a.pdf"),
    )
    management_types = [
        ManagementType(
            id="rice",
            name="水稲経営",
            premise=Premise(),
            growing_area=GrowingAreaList(items=None),
            balance=Balance(),
            capital_equipment=CapitalEquipmentList(items=None),
        )
    ]
    indicators = [
        ManagementIndicator(
            id="rice-main",
            crop_name="水稲（主食用）",
            balance=IndicatorBalance(),
            work_schedule=WorkScheduleList(term_unit="上下旬", items=None),
            work_technologies=WorkTechnologyList(items=None),
        )
    ]

    submission = baseline._build_submission(
        context=context,
        management_types=management_types,
        management_indicators=indicators,
    )

    assert submission.prefecture_name == "tokyo"
    assert submission.id == "a"
    assert submission.management_types[0].id == "rice"
    assert submission.management_indicators[0].id == "rice-main"
    assert submission.management_indicators[0].crop_name == "水稲（主食用）"


def test_parse_args_accepts_log_level():
    args = baseline.parse_args(
        ["-d", "/tmp/data", "-s", "/tmp/submission.jsonl", "--log-level", "DEBUG"]
    )
    assert str(args.data_dir) == "/tmp/data"
    assert str(args.submission) == "/tmp/submission.jsonl"
    assert args.log_level == "DEBUG"


def test_configure_logging_keeps_third_party_debug_suppressed():
    app_logger = logging.getLogger("dagri_subtask1_baseline")
    third_party_logger = logging.getLogger("httpx")
    root_logger = logging.getLogger()

    previous_root_level = root_logger.level
    previous_app_level = app_logger.level
    previous_app_propagate = app_logger.propagate
    previous_app_handlers = list(app_logger.handlers)

    try:
        baseline.configure_logging("DEBUG")

        assert root_logger.level == logging.WARNING
        assert app_logger.isEnabledFor(logging.DEBUG)
        assert app_logger.propagate is False
        assert len(app_logger.handlers) == 1
        assert not third_party_logger.isEnabledFor(logging.DEBUG)
        assert third_party_logger.isEnabledFor(logging.WARNING)
    finally:
        root_logger.setLevel(previous_root_level)
        app_logger.setLevel(previous_app_level)
        app_logger.propagate = previous_app_propagate
        app_logger.handlers.clear()
        app_logger.handlers.extend(previous_app_handlers)


def test_run_baseline_writes_one_submission_per_pdf(monkeypatch, tmp_path):
    input_dir = tmp_path / "dataset" / "test" / "input" / "tokyo"
    input_dir.mkdir(parents=True)
    (input_dir / "a.pdf").write_bytes(b"%PDF")
    submission_path = tmp_path / "submission.jsonl"

    monkeypatch.setattr(baseline, "create_llm_runtime_from_env", lambda: object())
    monkeypatch.setattr(baseline, "extract_text_from_pdf", lambda _path: "dummy text\fpage2")
    monkeypatch.setattr(
        baseline,
        "extract_management_types",
        lambda **_kwargs: [
            ManagementType(
                id="rice",
                name="水稲経営",
                premise=Premise(),
                growing_area=GrowingAreaList(items=None),
                balance=Balance(),
                capital_equipment=CapitalEquipmentList(items=None),
            )
        ],
    )
    monkeypatch.setattr(
        baseline,
        "extract_management_indicators",
        lambda **_kwargs: [
            ManagementIndicator(
                id="rice-main",
                crop_name="水稲",
                balance=IndicatorBalance(),
                work_schedule=WorkScheduleList(term_unit="上下旬", items=None),
                work_technologies=WorkTechnologyList(items=None),
            )
        ],
    )

    dataset = baseline.run_baseline(data_dir=tmp_path / "dataset", submission_path=submission_path)

    assert len(dataset.items) == 1
    lines = submission_path.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 1
    payload = json.loads(lines[0])
    assert payload["prefecture_name"] == "tokyo"
    assert payload["id"] == "a"
    assert payload["management_types"][0]["id"] == "rice"
    assert payload["management_indicators"][0]["id"] == "rice-main"


def test_run_baseline_falls_back_to_empty_values_on_failure(monkeypatch, tmp_path):
    input_dir = tmp_path / "dataset" / "test" / "input" / "tokyo"
    input_dir.mkdir(parents=True)
    (input_dir / "a.pdf").write_bytes(b"%PDF")
    submission_path = tmp_path / "submission.jsonl"

    monkeypatch.setattr(baseline, "create_llm_runtime_from_env", lambda: object())
    monkeypatch.setattr(
        baseline,
        "extract_text_from_pdf",
        lambda _path: (_ for _ in ()).throw(RuntimeError("broken pdf")),
    )

    baseline.run_baseline(data_dir=tmp_path / "dataset", submission_path=submission_path)

    payload = json.loads(submission_path.read_text(encoding="utf-8").strip())
    assert payload["management_types"] == []
    assert payload["management_indicators"] == []


def test_run_baseline_emits_warning_log_on_pdf_read_failure(monkeypatch, tmp_path, caplog):
    input_dir = tmp_path / "dataset" / "test" / "input" / "tokyo"
    input_dir.mkdir(parents=True)
    (input_dir / "a.pdf").write_bytes(b"%PDF")
    submission_path = tmp_path / "submission.jsonl"

    caplog.set_level(logging.WARNING, logger="dagri_subtask1_baseline")
    monkeypatch.setattr(baseline, "create_llm_runtime_from_env", lambda: object())
    monkeypatch.setattr(
        baseline,
        "extract_text_from_pdf",
        lambda _path: (_ for _ in ()).throw(RuntimeError("broken pdf")),
    )

    baseline.run_baseline(data_dir=tmp_path / "dataset", submission_path=submission_path)

    assert any("failed to read PDF" in rec.message for rec in caplog.records)


def test_run_baseline_emits_debug_log_on_processing(monkeypatch, tmp_path, caplog):
    input_dir = tmp_path / "dataset" / "test" / "input" / "tokyo"
    input_dir.mkdir(parents=True)
    (input_dir / "a.pdf").write_bytes(b"%PDF")
    submission_path = tmp_path / "submission.jsonl"

    caplog.set_level(logging.DEBUG, logger="dagri_subtask1_baseline")
    monkeypatch.setattr(baseline, "create_llm_runtime_from_env", lambda: object())
    monkeypatch.setattr(baseline, "extract_text_from_pdf", lambda _path: "dummy text")
    monkeypatch.setattr(
        baseline,
        "build_pdf_pages",
        lambda **_kwargs: [PDFPage(number=1, text="dummy")],
    )
    monkeypatch.setattr(baseline, "extract_management_types", lambda **_kwargs: [])
    monkeypatch.setattr(baseline, "extract_management_indicators", lambda **_kwargs: [])

    baseline.run_baseline(data_dir=tmp_path / "dataset", submission_path=submission_path)

    assert any("processing document" in rec.message for rec in caplog.records)


def test_run_baseline_keeps_temp_images_alive_during_extraction(monkeypatch, tmp_path):
    input_dir = tmp_path / "dataset" / "test" / "input" / "tokyo"
    input_dir.mkdir(parents=True)
    (input_dir / "a.pdf").write_bytes(b"%PDF")
    submission_path = tmp_path / "submission.jsonl"

    def _build_pdf_pages_stub(**kwargs):
        image_path = Path(kwargs["image_dir"]) / "page-1.png"
        image_path.write_bytes(b"png")
        return [PDFPage(number=1, text="dummy", image_path=image_path)]

    def _extract_management_types_stub(**kwargs):
        page = kwargs["pages"][0]
        # Reproduces the previous failure mode if temporary dir is already deleted.
        _ = page.image_path.read_bytes()  # type: ignore[union-attr]
        return [
            ManagementType(
                id="rice",
                name="水稲経営",
                premise=Premise(),
                growing_area=GrowingAreaList(items=None),
                balance=Balance(),
                capital_equipment=CapitalEquipmentList(items=None),
            )
        ]

    monkeypatch.setattr(baseline, "create_llm_runtime_from_env", lambda: object())
    monkeypatch.setattr(baseline, "extract_text_from_pdf", lambda _path: "dummy text")
    monkeypatch.setattr(baseline, "build_pdf_pages", _build_pdf_pages_stub)
    monkeypatch.setattr(baseline, "extract_management_types", _extract_management_types_stub)
    monkeypatch.setattr(baseline, "extract_management_indicators", lambda **_kwargs: [])

    dataset = baseline.run_baseline(data_dir=tmp_path / "dataset", submission_path=submission_path)

    assert len(dataset.items) == 1
    payload = json.loads(submission_path.read_text(encoding="utf-8").strip())
    assert payload["management_types"][0]["id"] == "rice"
