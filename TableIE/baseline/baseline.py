"""Baseline program for Subtask 1."""

from __future__ import annotations

import argparse
import logging
from dataclasses import dataclass
from pathlib import Path
from tempfile import TemporaryDirectory

from dagri_subtask1_baseline.management_indicator.pipeline import (
    extract_management_indicators,
)
from dagri_subtask1_baseline.management_type.pipeline import extract_management_types
from dagri_subtask1_baseline.shared.pdf_text_extractor import extract_text_from_pdf
from dagri_subtask1_baseline.shared.llm_client import create_llm_runtime_from_env
from dagri_subtask1_baseline.shared.logging_utils import debug, logger, warn
from dagri_subtask1_baseline.shared.pdf_pages import build_pdf_pages, split_text_into_pages
from dagri_subtask1_sdk.domain.management_indicator import ManagementIndicator
from dagri_subtask1_sdk.domain.management_type import ManagementType
from dagri_subtask1_sdk.domain.submission import Submission, SubmissionDataset
from dagri_subtask1_sdk.infra.agricultural_technical_pdf_document_discovery_service import (
    FileSystemAgriculturalTechnicalPDFDocumentDiscoveryService,
)
from dagri_subtask1_sdk.infra.submission_dataset_writer_service import (
    JsonlSubmissionDatasetWriterService,
)
from dagri_subtask1_sdk.usecase.create_submission_file_usecase import (
    CreateSubmissionFileUsecase,
)


@dataclass(frozen=True)
class ExtractorContext:
    prefecture_name: str
    file_id: str
    pdf_path: Path


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Baseline program for information extraction and structuring."
    )
    parser.add_argument(
        "-d",
        "--data-dir",
        type=Path,
        required=True,
        help="Path to the Subtask 1 dataset directory.",
    )
    parser.add_argument(
        "-s",
        "--submission",
        type=Path,
        required=True,
        help="Path to the submission JSONL file.",
    )
    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        default="INFO",
        help="Logging level for baseline processing.",
    )
    return parser.parse_args(argv)


def _build_submission(
    context: ExtractorContext,
    management_types: list[ManagementType],
    management_indicators: list[ManagementIndicator],
) -> Submission:
    return Submission(
        prefecture_name=context.prefecture_name,
        id=context.file_id,
        management_types=management_types,
        management_indicators=management_indicators,
    )


def run_baseline(data_dir: Path, submission_path: Path) -> SubmissionDataset:
    discovery_service = FileSystemAgriculturalTechnicalPDFDocumentDiscoveryService()
    documents = discovery_service.discover(data_dir=data_dir)
    llm_runtime = create_llm_runtime_from_env()
    debug(f"run_baseline started: data_dir={data_dir} discovered_pdfs={len(documents)}")

    submissions: list[Submission] = []
    for document in documents:
        context = ExtractorContext(
            prefecture_name=document.prefecture_name,
            file_id=document.file_id,
            pdf_path=document.file_path,
        )
        debug(
            "processing document: "
            f"prefecture={context.prefecture_name} file_id={context.file_id} path={context.pdf_path}"
        )

        try:
            pdf_text = extract_text_from_pdf(document.file_path)
            debug(f"pdf text extracted: path={document.file_path} chars={len(pdf_text)}")
        except Exception as error:  # noqa: BLE001
            warn(f"failed to read PDF {document.file_path}: {error}")
            submissions.append(
                _build_submission(
                    context=context,
                    management_types=[],
                    management_indicators=[],
                )
            )
            continue

        with TemporaryDirectory(prefix="dagri-baseline-pages-") as tmp_dir:
            try:
                pages = build_pdf_pages(
                    pdf_path=document.file_path,
                    pdf_text=pdf_text,
                    image_dir=tmp_dir,
                    dpi=150,
                )
                debug(
                    f"pages built with images: path={document.file_path} "
                    f"pages={len(pages)} temp_dir={tmp_dir}"
                )
            except Exception as error:  # noqa: BLE001
                warn(
                    f"failed to build page images from {document.file_path}: {error}. "
                    "fallback to text-only pages."
                )
                pages = split_text_into_pages(pdf_text)
                debug(
                    f"fallback to text-only pages: path={document.file_path} pages={len(pages)}"
                )

            try:
                management_types = extract_management_types(
                    pages=pages,
                    llm_runtime=llm_runtime,
                )
                debug(
                    f"management_types extracted: path={document.file_path} "
                    f"count={len(management_types)}"
                )
            except Exception as error:  # noqa: BLE001
                warn(f"failed to extract management_types from {document.file_path}: {error}")
                management_types = []

            try:
                management_indicators = extract_management_indicators(
                    pages=pages,
                    management_types=management_types,
                    llm_runtime=llm_runtime,
                )
                debug(
                    f"management_indicators extracted: path={document.file_path} "
                    f"count={len(management_indicators)}"
                )
            except Exception as error:  # noqa: BLE001
                warn(f"failed to extract management_indicators from {document.file_path}: {error}")
                management_indicators = []

            submissions.append(
                _build_submission(
                    context=context,
                    management_types=management_types,
                    management_indicators=management_indicators,
                )
            )

    submission_dataset = SubmissionDataset(items=submissions)
    usecase = CreateSubmissionFileUsecase(
        submission_dataset_writer_service=JsonlSubmissionDatasetWriterService()
    )
    usecase.execute(
        submission_dataset=submission_dataset,
        output_file_path=submission_path,
    )
    debug(
        "submission file written: "
        f"output={submission_path} items={len(submission_dataset.items)}"
    )
    return submission_dataset


def configure_logging(log_level: str) -> None:
    """Configure application logging without enabling verbose third-party debug logs.

    Design:
    - Root logger stays at WARNING so third-party DEBUG logs do not appear.
    - Baseline logger gets a dedicated handler and honors CLI `--log-level`.
    """

    app_level = getattr(logging, log_level)
    formatter = logging.Formatter("%(levelname)s %(name)s: %(message)s")

    root_logger = logging.getLogger()
    root_logger.setLevel(logging.WARNING)

    app_logger = logging.getLogger("dagri_subtask1_baseline")
    app_logger.setLevel(app_level)
    app_logger.propagate = False

    # Reconfigure to avoid duplicate lines when main() is invoked more than once.
    app_logger.handlers.clear()
    app_handler = logging.StreamHandler()
    app_handler.setLevel(app_level)
    app_handler.setFormatter(formatter)
    app_logger.addHandler(app_handler)

    # Extension point:
    # add the same handler to "dagri_subtask1_sdk" if SDK logs should be surfaced.


def main() -> None:
    args = parse_args()
    configure_logging(args.log_level)
    logger.debug(
        "main started: "
        f"data_dir={args.data_dir} submission={args.submission} log_level={args.log_level}"
    )
    dataset = run_baseline(data_dir=args.data_dir, submission_path=args.submission)
    logger.info(f"baseline finished: submissions={len(dataset.items)}")
    print(f"discovered_pdf_count: {len(dataset.items)}")
    print(f"submission: {args.submission}")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.warning("interrupted")
        raise
