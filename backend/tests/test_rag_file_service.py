from __future__ import annotations

import io

import pytest
from docx import Document

from app.services.rag_file_service import RAGFileParseError, RAGFileService


def _docx_bytes(*paragraphs: str) -> bytes:
    document = Document()
    for paragraph in paragraphs:
        document.add_paragraph(paragraph)
    buffer = io.BytesIO()
    document.save(buffer)
    return buffer.getvalue()


def test_extract_text_from_docx_bytes() -> None:
    service = RAGFileService()
    payload = _docx_bytes(
        "AIML placement handbook for Python projects.",
        "Students should complete capstone reviews before placement labs.",
    )

    text = service.extract_text("placement-handbook.docx", payload)

    assert "AIML placement handbook" in text
    assert "capstone reviews" in text


def test_extract_text_from_pdf_bytes(monkeypatch) -> None:
    class _Page:
        def __init__(self, text: str) -> None:
            self._text = text

        def extract_text(self) -> str:
            return self._text

    class _Reader:
        def __init__(self, _stream) -> None:
            self.pages = [
                _Page("Counseling policy for scholarship guidance."),
                _Page("Follow-up should happen within seven days."),
            ]

    monkeypatch.setattr("app.services.rag_file_service.PdfReader", _Reader)
    service = RAGFileService()

    text = service.extract_text("counseling-policy.pdf", b"%PDF fake bytes")

    assert "Counseling policy" in text
    assert "seven days" in text


def test_rejects_unsupported_file_extension() -> None:
    service = RAGFileService()

    with pytest.raises(RAGFileParseError, match="Only PDF or DOCX"):
        service.extract_text("notes.txt", b"plain text")


def test_rejects_oversized_file() -> None:
    service = RAGFileService(max_bytes=4)

    with pytest.raises(RAGFileParseError, match="exceeds allowed size"):
        service.extract_text("large.pdf", b"12345")


def test_rejects_files_without_extractable_text() -> None:
    service = RAGFileService()
    payload = _docx_bytes("   ", "")

    with pytest.raises(RAGFileParseError, match="extractable text"):
        service.extract_text("empty.docx", payload)
