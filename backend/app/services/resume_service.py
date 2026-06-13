from __future__ import annotations

import io
import re
from pathlib import Path
from typing import Iterable
from urllib.parse import parse_qs, quote, unquote, urlparse
from uuid import uuid4

from docx import Document
import httpx
from pypdf import PdfReader
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.scoring import RESUME_SCORING
from app.models.resume_analysis import ResumeAnalysis
from app.models.student_profile import StudentProfile
from app.services.llm_client import LLMClient
from app.utils.url_safety import validate_external_resume_url

STORAGE_ROOT = Path("storage/resumes")
MAX_BYTES = 5 * 1024 * 1024
ALLOWED_EXTS = {".pdf", ".docx"}
ALLOWED_CONTENT_TYPES = {
    "application/pdf": ".pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": ".docx",
    "application/msword": ".docx",
}
GENERIC_DOWNLOAD_CONTENT_TYPES = {
    "",
    "application/octet-stream",
    "binary/octet-stream",
    "application/download",
    "application/force-download",
    "application/x-download",
}

KNOWN_SKILLS = {
    "python",
    "sql",
    "java",
    "javascript",
    "typescript",
    "c++",
    "c",
    "react",
    "node",
    "django",
    "fastapi",
    "flask",
    "pytorch",
    "tensorflow",
    "scikit-learn",
    "pandas",
    "numpy",
    "power bi",
    "tableau",
    "git",
    "docker",
    "kubernetes",
    "aws",
    "azure",
    "gcp",
    "spark",
    "hadoop",
    "nlp",
    "mlops",
}

INDUSTRY_KEYWORDS = {
    "ai": {"machine learning", "deep learning", "nlp", "mlops", "pytorch", "tensorflow"},
    "ml": {"machine learning", "deep learning", "feature engineering", "mlops"},
    "data": {"statistics", "sql", "python", "pandas", "machine learning"},
    "backend": {"api", "database", "sql", "python", "java", "node", "system design"},
}


class ResumeFetchError(ValueError):
    def __init__(self, message: str, status_code: int = 400) -> None:
        super().__init__(message)
        self.status_code = status_code


class ResumeService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_latest_by_profile(self, profile_id: int) -> ResumeAnalysis | None:
        stmt = (
            select(ResumeAnalysis)
            .where(ResumeAnalysis.student_profile_id == profile_id)
            .order_by(ResumeAnalysis.created_at.desc())
        )
        return self.db.scalar(stmt)

    def create_analysis(
        self,
        profile: StudentProfile,
        file_name: str,
        data: bytes,
        *,
        source_url: str | None = None,
    ) -> ResumeAnalysis:
        normalized_name = self._normalize_source_file_name(file_name)
        self._validate_file(normalized_name, data)
        stored_name = self._store_file(profile.id, normalized_name, data)
        text = self._extract_text(stored_name, data)
        parsed = self._parse_resume(text, profile)
        analysis = ResumeAnalysis(
            student_profile_id=profile.id,
            file_name=stored_name,
            source_url=source_url,
            extracted_skills=parsed["skills"],
            projects=parsed["projects"],
            experience=parsed["experience"],
            education=parsed["education"],
            resume_score=parsed["score"],
            missing_keywords=parsed["missing_keywords"],
            weak_sections=parsed["weak_sections"],
            suggestions=parsed["suggestions"],
        )
        self.db.add(analysis)
        self.db.commit()
        self.db.refresh(analysis)
        return analysis

    def create_analysis_from_url(self, profile: StudentProfile, resume_url: str) -> ResumeAnalysis:
        safe_url = self._normalize_resume_url(resume_url)
        file_name, payload = self._fetch_resume_bytes(safe_url)
        return self.create_analysis(profile, file_name, payload, source_url=safe_url)

    def _normalize_resume_url(self, resume_url: str) -> str:
        settings = get_settings()
        safe_url = validate_external_resume_url(
            resume_url,
            allow_http=settings.resume_url_allow_http,
            validate_dns=settings.resume_url_validate_dns,
            max_length=settings.resume_url_max_length,
        )
        parsed = urlparse(safe_url)
        host = (parsed.hostname or "").lower()
        if host.endswith("drive.google.com"):
            file_id = self._extract_drive_file_id(parsed.path, parsed.query)
            if file_id:
                return (
                    "https://drive.google.com/uc?export=download&id="
                    f"{quote(file_id, safe='')}"
                )
        return safe_url

    def _extract_drive_file_id(self, path: str, query: str) -> str | None:
        match = re.search(r"/file/d/([^/]+)", path)
        if match:
            return unquote(match.group(1))
        query_values = parse_qs(query)
        if query_values.get("id"):
            return query_values["id"][0]
        return None

    def _fetch_resume_bytes(self, safe_url: str) -> tuple[str, bytes]:
        settings = get_settings()
        timeout = httpx.Timeout(settings.resume_fetch_timeout_seconds)
        headers = {"User-Agent": "AICareerAdvisor/1.0"}

        try:
            with httpx.Client(timeout=timeout, follow_redirects=True, headers=headers) as client:
                with client.stream("GET", safe_url) as response:
                    if response.status_code >= 400:
                        raise ResumeFetchError(
                            f"Unable to fetch resume URL (status {response.status_code}).",
                            status_code=502,
                        )

                    content_type = (
                        response.headers.get("content-type", "").split(";", 1)[0].strip().lower()
                    )
                    content_length = response.headers.get("content-length")
                    if content_length and int(content_length) > settings.resume_fetch_max_bytes:
                        raise ResumeFetchError(
                            "Resume file exceeds allowed size limit.",
                            status_code=400,
                        )

                    chunks: list[bytes] = []
                    total_size = 0
                    for chunk in response.iter_bytes():
                        total_size += len(chunk)
                        if total_size > settings.resume_fetch_max_bytes:
                            raise ResumeFetchError(
                                "Resume file exceeds allowed size limit.",
                                status_code=400,
                            )
                        chunks.append(chunk)

                    payload = b"".join(chunks)
                    detected_ext = self._detect_remote_file_extension(
                        safe_url,
                        content_type,
                        response.headers.get("content-disposition", ""),
                        payload,
                    )
                    if detected_ext is None:
                        raise ResumeFetchError(
                            "Resume URL content type is not supported (only PDF or DOCX).",
                            status_code=400,
                        )
                    file_name = self._determine_remote_file_name(
                        safe_url,
                        content_type,
                        response.headers.get("content-disposition", ""),
                        detected_ext=detected_ext,
                    )
                    return file_name, payload
        except httpx.TimeoutException as exc:
            raise ResumeFetchError("Resume URL fetch timed out.", status_code=504) from exc
        except httpx.HTTPError as exc:
            raise ResumeFetchError("Failed to download resume from URL.", status_code=502) from exc

    def _determine_remote_file_name(
        self,
        safe_url: str,
        content_type: str,
        content_disposition: str,
        *,
        detected_ext: str | None = None,
    ) -> str:
        disposition_match = re.search(r"filename\*=UTF-8''([^;]+)|filename=\"?([^\";]+)\"?", content_disposition)
        if disposition_match:
            candidate = disposition_match.group(1) or disposition_match.group(2)
            if candidate:
                candidate_name = Path(candidate).name
                if Path(candidate_name).suffix.lower() in ALLOWED_EXTS:
                    return candidate_name

        parsed = urlparse(safe_url)
        path_name = Path(parsed.path).name
        suffix = Path(path_name).suffix.lower()
        if suffix in ALLOWED_EXTS:
            return path_name

        return f"resume{detected_ext or ALLOWED_CONTENT_TYPES.get(content_type, '.pdf')}"

    def _detect_remote_file_extension(
        self,
        safe_url: str,
        content_type: str,
        content_disposition: str,
        payload: bytes,
    ) -> str | None:
        if content_type in ALLOWED_CONTENT_TYPES:
            return ALLOWED_CONTENT_TYPES[content_type]

        sniffed_ext = self._sniff_resume_extension(payload)
        if sniffed_ext:
            return sniffed_ext

        if content_type and content_type not in GENERIC_DOWNLOAD_CONTENT_TYPES:
            return None

        disposition_match = re.search(r"filename\*=UTF-8''([^;]+)|filename=\"?([^\";]+)\"?", content_disposition)
        if disposition_match:
            candidate = disposition_match.group(1) or disposition_match.group(2)
            if candidate:
                suffix = Path(candidate).suffix.lower()
                if suffix in ALLOWED_EXTS:
                    return suffix

        suffix = Path(urlparse(safe_url).path).suffix.lower()
        if suffix in ALLOWED_EXTS:
            return suffix
        return None

    def _sniff_resume_extension(self, payload: bytes) -> str | None:
        if payload.startswith(b"%PDF"):
            return ".pdf"
        if payload.startswith(b"PK\x03\x04") or payload.startswith(b"PK\x05\x06"):
            return ".docx"
        return None

    def _normalize_source_file_name(self, file_name: str) -> str:
        source = (file_name or "").strip()
        if source.lower().startswith(("http://", "https://")):
            settings = get_settings()
            safe_url = validate_external_resume_url(
                source,
                allow_http=settings.resume_url_allow_http,
                validate_dns=settings.resume_url_validate_dns,
                max_length=settings.resume_url_max_length,
            )
            parsed = urlparse(safe_url)
            return Path(parsed.path).name or "resume.pdf"

        return Path(source).name or "resume.pdf"

    def _validate_file(self, file_name: str, data: bytes) -> None:
        ext = Path(file_name).suffix.lower()
        if ext not in ALLOWED_EXTS:
            raise ValueError("Only PDF or DOCX files are supported.")
        if len(data) > MAX_BYTES:
            raise ValueError("File too large. Max size is 5MB.")

    def _store_file(self, profile_id: int, file_name: str, data: bytes) -> str:
        ext = Path(file_name).suffix.lower()
        safe_name = f"{uuid4().hex}{ext}"
        target_dir = STORAGE_ROOT / str(profile_id)
        target_dir.mkdir(parents=True, exist_ok=True)
        target_path = target_dir / safe_name
        target_path.write_bytes(data)
        return safe_name

    def _extract_text(self, stored_name: str, data: bytes) -> str:
        ext = Path(stored_name).suffix.lower()
        if ext == ".pdf":
            reader = PdfReader(io.BytesIO(data))
            return "\n".join(page.extract_text() or "" for page in reader.pages)
        if ext == ".docx":
            doc = Document(io.BytesIO(data))
            return "\n".join(paragraph.text for paragraph in doc.paragraphs)
        return ""

    def _parse_resume(self, text: str, profile: StudentProfile) -> dict[str, list[str] | int]:
        llm = LLMClient()
        try:
            analysis = llm.generate_resume_analysis(profile, text)
        except Exception as exc:
            raise ResumeFetchError("LLM resume analysis failed.", status_code=503) from exc

        return {
            "skills": analysis["extracted_skills"],
            "projects": analysis["projects"],
            "experience": analysis["experience"],
            "education": analysis["education"],
            "missing_keywords": analysis["missing_keywords"],
            "weak_sections": analysis["weak_sections"],
            "suggestions": analysis["suggestions"],
            "score": analysis["resume_score"],
        }

    def _normalize(self, text: str) -> str:
        return re.sub(r"\s+", " ", text.replace("\u2022", "\n")).replace("•", "\n")

    def _extract_section(self, lines: list[str], headers: Iterable[str]) -> list[str]:
        header_set = {h.lower() for h in headers}
        indices = []
        for idx, line in enumerate(lines):
            lower = line.lower().strip(":")
            if any(lower.startswith(header) for header in header_set):
                indices.append(idx)
        if not indices:
            return []
        start = indices[0] + 1
        end = next((i for i in range(start, len(lines)) if lines[i].isupper()), len(lines))
        return lines[start:end]

    def _parse_list_items(self, lines: list[str]) -> list[str]:
        items = []
        for line in lines:
            cleaned = re.sub(r"^[\-\*\d\.\)\s]+", "", line).strip()
            if cleaned:
                items.append(cleaned)
        return items[:10]

    def _parse_skills(self, skills_section: list[str], normalized: str) -> list[str]:
        if skills_section:
            joined = " ".join(skills_section)
            parts = re.split(r"[,\|/;]", joined)
            skills = [part.strip() for part in parts if part.strip()]
            return list(dict.fromkeys(skills))[:20]
        found = [skill for skill in KNOWN_SKILLS if skill in normalized.lower()]
        return sorted(found)

    def _missing_keywords(self, normalized: str, profile: StudentProfile) -> list[str]:
        text = normalized.lower()
        domain = f"{profile.target_industry} {profile.specialization}".lower()
        keywords: set[str] = set()
        for key, values in INDUSTRY_KEYWORDS.items():
            if key in domain:
                keywords |= values
        if not keywords:
            keywords = {"communication", "problem solving", "projects", "sql", "python"}
        return sorted([kw for kw in keywords if kw not in text])[:10]

    def _weak_sections(
        self,
        skills: list[str],
        projects: list[str],
        experience: list[str],
        education: list[str],
    ) -> list[str]:
        weak = []
        if len(skills) < 4:
            weak.append("skills")
        if not projects:
            weak.append("projects")
        if not experience:
            weak.append("experience")
        if not education:
            weak.append("education")
        return weak

    def _suggestions(self, weak_sections: list[str], missing_keywords: list[str]) -> list[str]:
        suggestions = []
        if "skills" in weak_sections:
            suggestions.append("Add a dedicated skills section with tools and technologies.")
        if "projects" in weak_sections:
            suggestions.append("Include 2-3 academic or personal projects with outcomes.")
        if "experience" in weak_sections:
            suggestions.append("Highlight internships, freelancing, or relevant coursework.")
        if missing_keywords:
            suggestions.append(
                f"Consider adding these keywords: {', '.join(missing_keywords[:5])}."
            )
        return suggestions[:6]

    def _resume_score(
        self,
        skills: list[str],
        projects: list[str],
        experience: list[str],
        education: list[str],
        profile: StudentProfile,
    ) -> int:
        config = RESUME_SCORING
        score = config.base_score
        score += min(len(skills) * config.skill_points_per_item, config.skill_points_cap)
        score += min(len(projects) * config.project_points_per_item, config.project_points_cap)
        score += min(
            len(experience) * config.experience_points_per_item,
            config.experience_points_cap,
        )
        score += config.education_points if education else 0
        score += config.certification_points if profile.certifications else 0
        return max(0, min(score, 100))
