import argparse
import sys

from dagri_subtask1_sdk.infra.submission_diagnose_service import (
    FileSystemSubmissionDiagnoseService,
)
from dagri_subtask1_sdk.usecase import DiagnoseSubmissionUsecase


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="提出ファイルの検査を行います。")
    parser.add_argument(
        "-s",
        "--submission",
        required=True,
        help="提出ファイル（JSONL）のパス",
    )
    parser.add_argument(
        "-d",
        "--data-dir",
        required=True,
        help="サブタスク1のデータセットディレクトリのパス",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    usecase = DiagnoseSubmissionUsecase(
        submission_diagnose_service=FileSystemSubmissionDiagnoseService()
    )
    result = usecase.execute(
        submission_file_path=args.submission,
        subtask1_data_dir=args.data_dir,
    )

    if result.is_valid:
        print("OK")
        return 0

    for error in result.errors:
        print(error)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
