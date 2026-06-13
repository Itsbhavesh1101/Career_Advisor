from __future__ import annotations

import hashlib
import json

from app.models.student_profile import StudentProfile
from app.services.llm_client import LLMClient


def _program_options_cache_hash(program_options: list[dict]) -> str:
    allowed_fields = (
        "program_id",
        "program_name",
        "school",
        "priority_skills",
        "career_paths",
        "admission_fit_signals",
        "reality_checks",
    )
    bounded_options: list[dict] = []
    for option in program_options:
        if option.get("is_active") is False:
            continue
        canonical_option = {
            field: option[field]
            for field in allowed_fields
            if field in option and option[field] is not None
        }
        if canonical_option.get("program_id"):
            bounded_options.append(canonical_option)
        if len(bounded_options) >= 12:
            break
    canonical_options = json.dumps(
        bounded_options,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        default=str,
    )
    return hashlib.sha256(canonical_options.encode("utf-8")).hexdigest()[:16]


def _rag_context_cache_hash(rag_context: list[dict] | None) -> str:
    allowed_fields = ("source_title", "source_type", "excerpt")
    bounded_context: list[dict] = []
    for item in rag_context or []:
        canonical_item = {
            field: item[field]
            for field in allowed_fields
            if field in item and item[field] is not None
        }
        if canonical_item.get("source_title") and canonical_item.get("excerpt"):
            bounded_context.append(canonical_item)
        if len(bounded_context) >= 5:
            break
    canonical_context = json.dumps(
        bounded_context,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        default=str,
    )
    return hashlib.sha256(canonical_context.encode("utf-8")).hexdigest()[:16]


class CareerAIEngine:
    def __init__(self, use_llm: bool = True) -> None:
        self.use_llm = use_llm
        self._llm_client = LLMClient() if use_llm else None
        self._llm_cache: dict[str, dict] = {}
        self._career_analysis_source = "unknown"
        self._branch_analysis_source = "not_applicable"
        self._program_fit_analysis_source = "rule_engine"

    @property
    def career_analysis_source(self) -> str:
        return self._career_analysis_source

    @property
    def branch_analysis_source(self) -> str:
        return self._branch_analysis_source

    @property
    def program_fit_analysis_source(self) -> str:
        return self._program_fit_analysis_source

    def _require_llm_client(self) -> LLMClient:
        if not self.use_llm:
            raise RuntimeError("LLM-only mode is enabled; rule engine is disabled")
        if self._llm_client is None or self._llm_client.client is None:
            raise RuntimeError("LLM client is not configured")
        return self._llm_client

    def _get_llm_output(self, profile: StudentProfile) -> dict:
        client = self._require_llm_client()
        profile_id = profile.id
        if profile_id is None:
            raise ValueError("Profile ID is required for LLM caching.")

        cache_key = f"career_{profile_id}"
        if cache_key not in self._llm_cache:
            self._llm_cache[cache_key] = client.generate_career_analysis(profile)
        self._career_analysis_source = "llm"
        return self._llm_cache[cache_key]

    def _get_branch_llm_output(self, profile: StudentProfile) -> dict:
        client = self._require_llm_client()
        profile_id = profile.id
        if profile_id is None:
            raise ValueError("Profile ID is required for LLM caching.")

        cache_key = f"branch_{profile_id}"
        if cache_key not in self._llm_cache:
            self._llm_cache[cache_key] = client.generate_branch_analysis(profile)
        self._branch_analysis_source = "llm"
        return self._llm_cache[cache_key]

    def _get_program_fit_llm_output(
        self,
        profile: StudentProfile,
        program_options: list[dict],
        catalog_version: str,
        rag_context: list[dict] | None = None,
    ) -> dict:
        client = self._require_llm_client()
        profile_id = profile.id
        if profile_id is None:
            raise ValueError("Profile ID is required for LLM caching.")

        options_hash = _program_options_cache_hash(program_options)
        rag_hash = _rag_context_cache_hash(rag_context)
        cache_key = f"program_fit_{profile_id}_{catalog_version}_{options_hash}_{rag_hash}"
        if cache_key not in self._llm_cache:
            self._llm_cache[cache_key] = client.generate_program_fit_analysis(
                profile,
                program_options,
                catalog_version,
                rag_context=rag_context,
            )
        self._program_fit_analysis_source = "llm"
        return self._llm_cache[cache_key]

    def generate_career_recommendations(self, profile: StudentProfile) -> list[dict]:
        return self._get_llm_output(profile)["career_recommendations"]

    def generate_skill_gaps(self, profile: StudentProfile) -> list[dict]:
        return self._get_llm_output(profile)["skill_gaps"]

    def generate_learning_roadmap(self, profile: StudentProfile) -> list[dict]:
        return self._get_llm_output(profile)["learning_roadmap"]

    def generate_salary_insights(self, profile: StudentProfile) -> dict:
        return self._get_llm_output(profile)["salary_insights"]

    def generate_industry_trends(self, profile: StudentProfile) -> list[dict]:
        return self._get_llm_output(profile)["industry_trends"]

    def generate_branch_analysis(self, profile: StudentProfile) -> dict:
        return self._get_branch_llm_output(profile)

    def generate_program_fit_analysis(
        self,
        profile: StudentProfile,
        program_options: list[dict],
        catalog_version: str,
        rag_context: list[dict] | None = None,
    ) -> dict:
        return self._get_program_fit_llm_output(
            profile,
            program_options,
            catalog_version,
            rag_context=rag_context,
        )
