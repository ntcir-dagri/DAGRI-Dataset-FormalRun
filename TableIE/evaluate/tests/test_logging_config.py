import json
import logging

from dagri_subtask1_eval.main.logging_config import JsonLogFormatter


def test_json_log_formatter_outputs_json() -> None:
    formatter = JsonLogFormatter()
    record = logging.LogRecord(
        name="dagri_subtask1_eval.usecase.evaluate_usecase",
        level=logging.INFO,
        pathname=__file__,
        lineno=1,
        msg="field_evaluation",
        args=(),
        exc_info=None,
    )
    record.event_data = {
        "category": "management_type",
        "field_name": "note",
        "score": 1.0,
    }

    formatted = formatter.format(record)

    assert json.loads(formatted) == {
        "level": "INFO",
        "logger": "dagri_subtask1_eval.usecase.evaluate_usecase",
        "message": "field_evaluation",
        "category": "management_type",
        "field_name": "note",
        "score": 1.0,
    }
