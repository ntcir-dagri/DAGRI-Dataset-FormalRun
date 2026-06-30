from pathlib import Path

from dagri_subtask1_sdk.domain.agricultural_technical_pdf_document import (
    AgriculturalTechnicalPDFDocument,
)
from dagri_subtask1_sdk.domain.agricultural_technical_pdf_document_discovery_service import (
    AgriculturalTechnicalPDFDocumentDiscoveryService,
)


class FileSystemAgriculturalTechnicalPDFDocumentDiscoveryService(
    AgriculturalTechnicalPDFDocumentDiscoveryService
):
    def discover(self, data_dir: str | Path) -> list[AgriculturalTechnicalPDFDocument]:
        data_root = Path(data_dir)
        candidate_roots = [
            data_root,
        ]
        roots = [root for root in candidate_roots if root.exists() and root.is_dir()]
        if not roots:
            return []

        documents: list[AgriculturalTechnicalPDFDocument] = []
        for root in roots:
            for pdf_file in root.rglob("*.pdf"):
                relative_path = pdf_file.relative_to(root)
                if len(relative_path.parts) != 2:
                    continue

                prefecture_name = relative_path.parts[0]
                file_id = Path(relative_path.parts[1]).stem
                if not prefecture_name or not file_id:
                    continue

                documents.append(
                    AgriculturalTechnicalPDFDocument(
                        prefecture_name=prefecture_name,
                        file_id=file_id,
                        file_path=pdf_file,
                    )
                )

        return sorted(
            documents,
            key=lambda document: (document.prefecture_name, document.file_id),
        )
