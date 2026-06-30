from dagri_subtask1_eval.domain.eval_dataset import EvalData, EvalDataset
from dagri_subtask1_eval.domain.submission import Submission, SubmissionDataset


def test_validate_item_keys_returns_true_when_keys_match() -> None:
    submission_dataset = SubmissionDataset(
        items=[
            Submission(
                prefecture_name="tokyo",
                id="1",
                management_types=[],
                management_indicators=[],
            ),
            Submission(
                prefecture_name="osaka",
                id="2",
                management_types=[],
                management_indicators=[],
            ),
        ]
    )
    eval_dataset = EvalDataset(
        items=[
            EvalData(
                prefecture_name="osaka",
                id="2",
                management_types=[],
                management_indicators=[],
            ),
            EvalData(
                prefecture_name="tokyo",
                id="1",
                management_types=[],
                management_indicators=[],
            ),
        ]
    )

    is_valid, missing_or_extra_keys = submission_dataset.validate_item_keys(eval_dataset)

    assert is_valid is True
    assert missing_or_extra_keys == []


def test_validate_item_keys_returns_symmetric_difference_when_keys_do_not_match() -> None:
    submission_dataset = SubmissionDataset(
        items=[
            Submission(
                prefecture_name="tokyo",
                id="1",
                management_types=[],
                management_indicators=[],
            ),
            Submission(
                prefecture_name="osaka",
                id="2",
                management_types=[],
                management_indicators=[],
            ),
        ]
    )
    eval_dataset = EvalDataset(
        items=[
            EvalData(
                prefecture_name="tokyo",
                id="1",
                management_types=[],
                management_indicators=[],
            ),
            EvalData(
                prefecture_name="kyoto",
                id="3",
                management_types=[],
                management_indicators=[],
            ),
        ]
    )

    is_valid, missing_or_extra_keys = submission_dataset.validate_item_keys(eval_dataset)

    assert is_valid is False
    assert missing_or_extra_keys == [("kyoto", "3"), ("osaka", "2")]
