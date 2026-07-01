from __future__ import annotations

import argparse
import json

from .scoring import evaluate_submission


def main() -> None:
    # Provide a small CLI wrapper so the evaluator can run standalone.
    parser = argparse.ArgumentParser(
        description="Evaluate MTMH-QA submission accuracy from two JSONL files."
    )
    parser.add_argument(
        "--gold",
        required=True,
        help="Path to the ground-truth JSONL file.",
    )
    parser.add_argument(
        "--pred",
        required=True,
        help="Path to the participant submission JSONL file.",
    )
    parser.add_argument(
        "--indent",
        type=int,
        default=2,
        help="Indentation width for the JSON output.",
    )
    args = parser.parse_args()

    result = evaluate_submission(args.gold, args.pred)
    # JSON output is convenient for leaderboard systems and shell pipelines.
    print(json.dumps(result.to_dict(), ensure_ascii=False, indent=args.indent))


if __name__ == "__main__":
    main()
