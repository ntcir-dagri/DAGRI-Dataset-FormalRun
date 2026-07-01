"""Evaluation utilities for the MTMH-QA shared task."""

# Re-export the main public functions so leaderboard code can import them directly.
from .scoring import evaluate_submission, load_jsonl, score_answers

__all__ = ["evaluate_submission", "load_jsonl", "score_answers"]
