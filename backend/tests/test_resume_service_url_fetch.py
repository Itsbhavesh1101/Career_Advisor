from __future__ import annotations

import pytest

from app.services import resume_service as service_module
from app.services.resume_service import ResumeFetchError, ResumeService


def test_normalize_google_drive_share_url_to_download_url() -> None:
    service = ResumeService(db=None)  # type: ignore[arg-type]

    normalized = service._normalize_resume_url(  # type: ignore[attr-defined]
        "https://drive.google.com/file/d/1yUPEI1yKKC9i3wBeWI14EGLScPsKhxkV/view?usp=drive_link"
    )

    assert normalized == (
        "https://drive.google.com/uc?export=download&id="
        "1yUPEI1yKKC9i3wBeWI14EGLScPsKhxkV"
    )


def test_fetch_resume_bytes_accepts_drive_octet_stream_pdf(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    service = ResumeService(db=None)  # type: ignore[arg-type]
    pdf_payload = b"%PDF-1.4\nfake but signature is enough for fetch validation"

    class _FakeResponse:
        status_code = 200
        headers = {
            "content-type": "application/octet-stream",
            "content-disposition": 'attachment; filename="Aditi-Resume.pdf"',
            "content-length": str(len(pdf_payload)),
        }

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb) -> None:
            del exc_type, exc, tb

        def iter_bytes(self):
            yield pdf_payload

    class _FakeClient:
        def __init__(self, *args, **kwargs) -> None:
            del args, kwargs

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb) -> None:
            del exc_type, exc, tb

        def stream(self, method: str, url: str):
            assert method == "GET"
            assert url.endswith("export=download&id=resume-file")
            return _FakeResponse()

    monkeypatch.setattr(service_module.httpx, "Client", _FakeClient)

    file_name, payload = service._fetch_resume_bytes(  # type: ignore[attr-defined]
        "https://drive.google.com/uc?export=download&id=resume-file"
    )

    assert file_name == "Aditi-Resume.pdf"
    assert payload == pdf_payload


def test_fetch_resume_bytes_rejects_html_drive_interstitial(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    service = ResumeService(db=None)  # type: ignore[arg-type]

    class _FakeResponse:
        status_code = 200
        headers = {"content-type": "text/html"}

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb) -> None:
            del exc_type, exc, tb

        def iter_bytes(self):
            yield b"<html>Google Drive could not download this file</html>"

    class _FakeClient:
        def __init__(self, *args, **kwargs) -> None:
            del args, kwargs

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb) -> None:
            del exc_type, exc, tb

        def stream(self, method: str, url: str):
            del method, url
            return _FakeResponse()

    monkeypatch.setattr(service_module.httpx, "Client", _FakeClient)

    with pytest.raises(ResumeFetchError, match="PDF or DOCX"):
        service._fetch_resume_bytes("https://drive.google.com/uc?export=download&id=bad")  # type: ignore[attr-defined]
