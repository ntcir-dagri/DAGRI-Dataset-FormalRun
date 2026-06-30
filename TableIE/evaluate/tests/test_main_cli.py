import sys
from pathlib import Path

from dagri_subtask1_eval.main.cli import parse_args


def test_parse_args_reads_submission_and_eval_files(monkeypatch) -> None:
    monkeypatch.setattr(
        sys,
        "argv",
        ["prog", "submission.jsonl", "eval.jsonl"],
    )

    args = parse_args()

    assert args.submission_file == Path("submission.jsonl")
    assert args.eval_file == Path("eval.jsonl")
