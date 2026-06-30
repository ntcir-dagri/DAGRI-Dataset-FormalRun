from dagri_subtask1_sdk.infra.agricultural_technical_pdf_document_discovery_service import (
    FileSystemAgriculturalTechnicalPDFDocumentDiscoveryService,
)


def test_discover_collects_documents_from_expected_layout(tmp_path):
    input_dir = tmp_path / "dataset"
    (input_dir / "tokyo").mkdir(parents=True)
    (input_dir / "tokyo" / "a.pdf").write_bytes(b"%PDF")
    (input_dir / "osaka").mkdir(parents=True)
    (input_dir / "osaka" / "b.pdf").write_bytes(b"%PDF")

    service = FileSystemAgriculturalTechnicalPDFDocumentDiscoveryService()
    actual = service.discover(data_dir=tmp_path / "dataset")

    assert len(actual) == 2
    assert actual[0].prefecture_name == "osaka"
    assert actual[0].file_id == "b"
    assert actual[0].file_path == input_dir / "osaka" / "b.pdf"
    assert actual[1].prefecture_name == "tokyo"
    assert actual[1].file_id == "a"
    assert actual[1].file_path == input_dir / "tokyo" / "a.pdf"


def test_discover_ignores_files_outside_expected_depth(tmp_path):
    input_dir = tmp_path / "dataset"
    input_dir.mkdir(parents=True)
    (input_dir / "readme.pdf").write_bytes(b"%PDF")
    (input_dir / "tokyo").mkdir()
    (input_dir / "tokyo" / "nested").mkdir()
    (input_dir / "tokyo" / "nested" / "c.pdf").write_bytes(b"%PDF")

    service = FileSystemAgriculturalTechnicalPDFDocumentDiscoveryService()
    actual = service.discover(data_dir=tmp_path / "dataset")

    assert actual == []


def test_discover_returns_sorted_by_prefecture_and_file_id(tmp_path):
    input_dir = tmp_path / "dataset"
    (input_dir / "tokyo").mkdir(parents=True)
    (input_dir / "tokyo" / "z.pdf").write_bytes(b"%PDF")
    (input_dir / "tokyo" / "a.pdf").write_bytes(b"%PDF")
    (input_dir / "aichi").mkdir(parents=True)
    (input_dir / "aichi" / "m.pdf").write_bytes(b"%PDF")

    service = FileSystemAgriculturalTechnicalPDFDocumentDiscoveryService()
    actual = service.discover(data_dir=tmp_path / "dataset")

    assert [(doc.prefecture_name, doc.file_id) for doc in actual] == [
        ("aichi", "m"),
        ("tokyo", "a"),
        ("tokyo", "z"),
    ]


def test_discover_returns_empty_when_no_pdfs(tmp_path):
    (tmp_path / "dataset").mkdir(parents=True)

    service = FileSystemAgriculturalTechnicalPDFDocumentDiscoveryService()
    actual = service.discover(data_dir=tmp_path / "dataset")

    assert actual == []


def test_discover_collects_documents_from_data_root_layout(tmp_path):
    input_dir = tmp_path / "train_input"
    (input_dir / "tokyo").mkdir(parents=True)
    (input_dir / "tokyo" / "a.pdf").write_bytes(b"%PDF")

    service = FileSystemAgriculturalTechnicalPDFDocumentDiscoveryService()
    actual = service.discover(data_dir=input_dir)

    assert len(actual) == 1
    assert actual[0].prefecture_name == "tokyo"
    assert actual[0].file_id == "a"
