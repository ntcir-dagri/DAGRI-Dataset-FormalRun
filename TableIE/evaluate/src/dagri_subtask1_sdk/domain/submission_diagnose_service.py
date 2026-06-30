import abc
import dataclasses


@dataclasses.dataclass
class SubmissionDiagnoseResult:
    is_valid: bool
    errors: list[str]


class SubmissionDiagnoseService(abc.ABC):
    @abc.abstractmethod
    def diagnose(
        self,
        submission_file: str,
        subtask1_data_dir: str,
    ) -> SubmissionDiagnoseResult:
        """提出ファイルのパスとサブタスク1のデータセットディレクトリのパスを指定して、
        ファイル中のサンプル数やJSON形式が有効か確認します。

        指定したデータセットディレクトリ `subtask1_data_dir` を起点に、
        `{{subtask1_data_dir}}/test/input/{{prefecture_name}}/{{file_id}}.pdf`
        を走査し、PDFファイルに対する解析結果が過不足なく提出ファイルに含まれているかを確認します。

        Arguments:
            submission_file: 提出ファイルのパス
            subtask1_data_dir: サブタスク1のデータセットが格納されているディレクトリのパス

        Returns:
            SubmissionDiagnoseResult: 診断結果
        """
