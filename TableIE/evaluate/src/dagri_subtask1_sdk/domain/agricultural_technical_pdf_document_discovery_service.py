import abc
from pathlib import Path

from .agricultural_technical_pdf_document import AgriculturalTechnicalPDFDocument


class AgriculturalTechnicalPDFDocumentDiscoveryService(abc.ABC):
    @abc.abstractmethod
    def discover(self, data_dir: str | Path) -> list[AgriculturalTechnicalPDFDocument]:
        """指定したデータディレクトリ配下から農業技術PDF文書を探索します。"""
