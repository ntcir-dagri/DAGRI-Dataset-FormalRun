from dagri_subtask1_eval.main.cli import parse_args
from dagri_subtask1_eval.main.container import build_evaluate_usecase
from dagri_subtask1_eval.main.logging_config import configure_logging


def main() -> None:
    configure_logging()
    args = parse_args()
    usecase = build_evaluate_usecase()
    score = usecase.execute(args.submission_file, args.eval_file)
    print(score)


if __name__ == "__main__":
    main()
