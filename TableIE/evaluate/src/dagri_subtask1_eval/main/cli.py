import argparse
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="dagri-subtask1-eval",
        description="Evaluate a submission file against a ground-truth dataset.",
    )
    parser.add_argument(
        "submission_file",
        type=Path,
        help="Path to the submission JSONL file.",
    )
    parser.add_argument(
        "eval_file",
        type=Path,
        help="Path to the evaluation JSONL file.",
    )
    return parser.parse_args()
