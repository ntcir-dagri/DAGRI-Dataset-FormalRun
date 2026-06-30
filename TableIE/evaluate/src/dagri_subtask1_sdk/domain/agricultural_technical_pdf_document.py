from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class AgriculturalTechnicalPDFDocument:
    prefecture_name: str
    file_id: str
    file_path: Path
