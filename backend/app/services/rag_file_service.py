from __future__ import annotations

import io
import re
from pathlib import Path

from docx import Document
from pypdf import PdfReader

MAX_RAG_UPLOAD_BYTES = 10 * 1024 * 1024
ALLOWED_RAG_FILE_EXTS = {".pdf", ".docx"}


class RAGFileParseError(ValueError):
    def __init__(self, message: str, status_code: int = 400) -> None:
        super().__init__(message)
        self.status_code = status_code


class RAGFileService:
    def __init__(self, *, max_bytes: int = MAX_RAG_UPLOAD_BYTES) -> None:
        self.max_bytes = max_bytes

    def extract_text(self, file_name: str, data: bytes) -> str:
        normalized_name = Path(file_name or "").name
        ext = Path(normalized_name).suffix.lower()
        if ext not in ALLOWED_RAG_FILE_EXTS:
            raise RAGFileParseError("Only PDF or DOCX knowledge files are supported.")
        if len(data) > self.max_bytes:
            raise RAGFileParseError("Knowledge file exceeds allowed size limit.")

        if ext == ".pdf":
            text = self._extract_pdf_text(data)
        else:
            text = self._extract_docx_text(data)

        normalized = self._normalize_text(text)
        if len(normalized) < 40:
            raise RAGFileParseError("Knowledge file does not contain enough extractable text.")
        return normalized

    def _extract_pdf_text(self, data: bytes) -> str:
        try:
            reader = PdfReader(io.BytesIO(data))
            return "\n".join(page.extract_text() or "" for page in reader.pages)
        except Exception as exc:
            raise RAGFileParseError("Unable to parse PDF knowledge file.") from exc

    def _extract_docx_text(self, data: bytes) -> str:
        try:
            document = Document(io.BytesIO(data))
            return "\n".join(paragraph.text for paragraph in document.paragraphs)
        except Exception as exc:
            raise RAGFileParseError("Unable to parse DOCX knowledge file.") from exc

    def _normalize_text(self, text: str) -> str:
        return re.sub(r"\s+", " ", text.replace("\u2022", " ")).strip()
