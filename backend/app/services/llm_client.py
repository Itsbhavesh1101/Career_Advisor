from __future__ import annotations

import json
import logging
import re
import time
from datetime import datetime, timedelta, timezone
from threading import Lock
from typing import Any

from pydantic import ValidationError

from app.core.config import get_settings
from app.models.student_profile import StudentProfile
from app.schemas.llm_outputs import (
    BranchAnalysisLLMOutput,
    CareerAnalysisLLMOutput,
    CompanyFitLLMOutput,
    CompanyFitAdjustments,
    EmployabilityScoreLLMOutput,
    EmployabilityAdjustments,
    IndustryTrendsOutput,
    InternshipReadinessLLMOutput,
    PlacementRiskLLMOutput,
    ProgramFitLLMOutput,
    ResumeAnalysisLLMOutput,
    RoleGapAnalysisLLMOutput,
    TrainingRecommendationsLLMOutput,
)
from app.schemas.psychometric_quiz import PsychometricQuestionLLMOutput
from app.services.llm_cost_control import (
    LLMRequestBudget,
    enforce_prompt_limit,
    enforce_token_limit,
    record_llm_event,
    record_llm_usage,
    reserve_llm_request,
)
from app.services.llm_providers import create_llm_provider
from app.services.institution_config_service import BRANDING_BY_MODE

logger = logging.getLogger(__name__)


class _CircuitBreaker:
    def __init__(self) -> None:
        self._lock = Lock()
        self._failure_count = 0
        self._opened_until: datetime | None = None

    def allow(self) -> bool:
        with self._lock:
            if self._opened_until is None:
                return True
            now = datetime.now(timezone.utc)
            if now >= self._opened_until:
                self._opened_until = None
                self._failure_count = 0
                return True
            return False

    def on_success(self) -> None:
        with self._lock:
            self._failure_count = 0
            self._opened_until = None

    def on_failure(self, threshold: int, reset_seconds: int) -> None:
        with self._lock:
            self._failure_count += 1
            if self._failure_count >= threshold:
                self._opened_until = datetime.now(timezone.utc) + timedelta(
                    seconds=reset_seconds
                )

    def state(self) -> dict[str, Any]:
        with self._lock:
            return {
                "failure_count": self._failure_count,
                "opened_until": self._opened_until.isoformat()
                if self._opened_until is not None
                else None,
            }


_BREAKER = _CircuitBreaker()


class LLMClient:
    def __init__(self) -> None:
        settings = get_settings()
        self._settings = settings
        self.model = (
            settings.bedrock_model_id
            if settings.llm_provider == "bedrock"
            else settings.openai_model
        )
        self.provider = create_llm_provider(settings)
        self.client = self.provider

    def _request_budget(self) -> LLMRequestBudget:
        settings = self._settings
        return LLMRequestBudget(
            daily_limit=settings.llm_daily_request_limit,
            user_daily_limit=settings.llm_user_daily_request_limit,
            prompt_max_chars=settings.llm_prompt_max_chars,
            output_token_cap=settings.llm_max_output_tokens,
            endpoint_daily_limits={
                "analysis": settings.llm_analysis_endpoint_daily_limit,
                "chat": settings.llm_chat_endpoint_daily_limit,
                "industry": settings.llm_industry_endpoint_daily_limit,
                "quiz_generation": settings.llm_quiz_endpoint_daily_limit,
                "program_fit": settings.llm_program_fit_endpoint_daily_limit,
            },
        )

    def _require_client(self):
        if self.provider is None:
            raise RuntimeError("LLM disabled")
        return self.provider

    def _safe_llm_call(
        self,
        *,
        endpoint: str,
        user_key: str,
        usage_scope: str = "global",
        system_prompt: str,
        user_prompt: str,
        temperature: float,
        max_output_tokens: int,
        expect_json: bool,
    ) -> str:
        if not _BREAKER.allow():
            record_llm_event(user_key=user_key, endpoint=endpoint, event="breaker_open")
            logger.warning(
                "llm_call_skipped breaker_open endpoint=%s user=%s state=%s",
                endpoint,
                user_key,
                _BREAKER.state(),
            )
            raise RuntimeError("LLM circuit breaker is open")

        provider = self._require_client()
        budget = self._request_budget()

        bounded_prompt = enforce_prompt_limit(user_prompt, budget.prompt_max_chars)
        bounded_tokens = enforce_token_limit(max_output_tokens, budget.output_token_cap)

        reserve_llm_request(budget, user_key=user_key, endpoint=endpoint)

        retries = self._settings.openai_max_retries
        last_exc: Exception | None = None
        start = time.perf_counter()

        for attempt in range(retries + 1):
            try:
                response = provider.complete(
                    model=self.model,
                    system_prompt=system_prompt,
                    user_prompt=bounded_prompt,
                    temperature=temperature,
                    max_output_tokens=bounded_tokens,
                    expect_json=expect_json,
                )
                output_text = response.text.strip()
                if not output_text:
                    raise ValueError("LLM returned empty response.")

                tokens = response.total_tokens
                usage_snapshot = record_llm_usage(
                    user_key=user_key,
                    endpoint=endpoint,
                    usage_scope=usage_scope,
                    prompt_chars=len(bounded_prompt),
                    output_chars=len(output_text),
                    total_tokens=tokens,
                )

                elapsed_ms = int((time.perf_counter() - start) * 1000)
                logger.info(
                    "llm_call_ok endpoint=%s user=%s latency_ms=%s retries=%s tokens=%s usage=%s breaker=%s",
                    endpoint,
                    user_key,
                    elapsed_ms,
                    attempt,
                    tokens,
                    usage_snapshot,
                    _BREAKER.state(),
                )
                record_llm_event(user_key=user_key, endpoint=endpoint, event="success")
                _BREAKER.on_success()
                return output_text
            except Exception as exc:
                last_exc = exc
                _BREAKER.on_failure(
                    threshold=self._settings.llm_circuit_breaker_threshold,
                    reset_seconds=self._settings.llm_circuit_breaker_reset_seconds,
                )
                logger.warning(
                    "llm_call_failed endpoint=%s user=%s attempt=%s breaker=%s error=%s",
                    endpoint,
                    user_key,
                    attempt,
                    _BREAKER.state(),
                    exc,
                )
                record_llm_event(user_key=user_key, endpoint=endpoint, event="failure")
                if attempt < retries:
                    time.sleep(0.5 * (attempt + 1))
                    continue

        raise RuntimeError("LLM request failed") from last_exc

    def _parse_json(self, output_text: str) -> dict[str, Any]:
        cleaned = output_text.strip()
        if cleaned.startswith("```"):
            cleaned = re.sub(r"^```[a-zA-Z]*", "", cleaned).strip()
            cleaned = cleaned.rstrip("`").strip()
        try:
            parsed = json.loads(cleaned)
            if isinstance(parsed, dict):
                return parsed
            raise ValueError("LLM response must be a JSON object.")
        except json.JSONDecodeError:
            match = re.search(r"\{.*\}", cleaned, re.DOTALL)
            if match:
                parsed = json.loads(match.group(0))
                if isinstance(parsed, dict):
                    return parsed
            raise ValueError("LLM returned invalid JSON.")

    def _repair_json_if_needed(
        self,
        *,
        endpoint: str,
        user_key: str,
        raw_text: str,
    ) -> dict[str, Any]:
        parse_error: Exception | None = None
        try:
            return self._parse_json(raw_text)
        except Exception as parse_exc:
            parse_error = parse_exc
            record_llm_event(user_key=user_key, endpoint=endpoint, event="parse_repair")
            logger.info(
                "llm_json_parse_failed endpoint=%s user=%s error=%s action=repair",
                endpoint,
                user_key,
                parse_exc,
            )

        try:
            repair_text = self._safe_llm_call(
                endpoint=f"{endpoint}_repair",
                user_key=user_key,
                system_prompt=(
                    "You fix malformed JSON for API ingestion. "
                    "Return only strict JSON object with no markdown."
                ),
                user_prompt=raw_text,
                temperature=0.0,
                max_output_tokens=500,
                expect_json=True,
            )
            repaired = self._parse_json(repair_text)
            logger.info("llm_json_repair_succeeded endpoint=%s user=%s", endpoint, user_key)
            return repaired
        except Exception as repair_exc:
            logger.warning(
                "llm_json_repair_failed endpoint=%s user=%s parse_error=%s repair_error=%s",
                endpoint,
                user_key,
                parse_error,
                repair_exc,
            )
            raise ValueError("LLM returned invalid JSON.") from repair_exc

    def _normalize_internship_readiness_payload(
        self,
        *,
        payload: dict[str, Any],
        user_key: str,
    ) -> dict[str, Any]:
        normalized = dict(payload)
        raw_level = normalized.get("readiness_level")
        raw_score = normalized.get("readiness_score")

        mapped_level: str | None = None
        if isinstance(raw_level, str):
            collapsed_level = " ".join(
                raw_level.strip().lower().replace("_", " ").replace("-", " ").split()
            )
            level_aliases = {
                "very low": "Low",
                "low": "Low",
                "beginner": "Low",
                "medium": "Medium",
                "moderate": "Medium",
                "average": "Medium",
                "mid": "Medium",
                "high": "High",
                "very high": "High",
                "advanced": "High",
            }
            mapped_level = level_aliases.get(collapsed_level)

        numeric_score: int | None = None
        if isinstance(raw_score, (int, float)) and not isinstance(raw_score, bool):
            numeric_score = int(raw_score)
        elif isinstance(raw_score, str):
            score_text = raw_score.strip()
            if score_text.isdigit():
                numeric_score = int(score_text)

        if mapped_level is None and numeric_score is not None:
            if numeric_score < 40:
                mapped_level = "Low"
            elif numeric_score < 70:
                mapped_level = "Medium"
            else:
                mapped_level = "High"

        if mapped_level is not None:
            if raw_level != mapped_level:
                logger.info(
                    "llm_schema_repaired endpoint=analysis user=%s field=readiness_level original=%s normalized=%s",
                    user_key,
                    raw_level,
                    mapped_level,
                )
            normalized["readiness_level"] = mapped_level

        return normalized

    def generate_career_analysis(self, profile: StudentProfile) -> dict[str, Any]:
        user_key = f"user:{profile.user_id}"
        system_prompt = (
            "You are an expert career advisor and labor market analyst. "
            "Analyze the student's profile and produce structured career insights. "
            "Recommendations must consider current skills, specialization, "
            "industry trends, realistic entry-level roles, and skill gaps required. "
            "Score each career path from 0 to 100. "
            "Skill gap priority must be: high | medium | low. "
            "Return ONLY valid JSON that matches the required schema."
        )
        user_prompt = (
            "Generate career insights for the following student profile.\n"
            f"Name: {profile.name}\n"
            f"Degree: {profile.degree}\n"
            f"Specialization: {profile.specialization}\n"
            f"Current Skills: {', '.join(profile.current_skills)}\n"
            f"Interests: {', '.join(profile.interests)}\n"
            f"Target Industry: {profile.target_industry}\n"
            "\n"
            "Required JSON format:\n"
            "{\n"
            '  "career_recommendations":[{"role":"AI Engineer","score":82}],\n'
            '  "skill_gaps":[{"skill":"Machine Learning","priority":"high"}],\n'
            '  "learning_roadmap":[{"stage":"Foundations","topics":["Python","Statistics"]}],\n'
            '  "salary_insights":{"currency":"INR","estimate_min":600000,"estimate_max":1200000},\n'
            '  "industry_trends":[{"trend":"AI Agents","impact":"high"}]\n'
            "}\n"
        )

        raw_text = self._safe_llm_call(
            endpoint="analysis",
            user_key=user_key,
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            temperature=0.7,
            max_output_tokens=600,
            expect_json=True,
        )
        data = self._repair_json_if_needed(
            endpoint="analysis",
            user_key=user_key,
            raw_text=raw_text,
        )
        try:
            validated = CareerAnalysisLLMOutput.model_validate(data)
            return validated.model_dump()
        except ValidationError as exc:
            record_llm_event(user_key=user_key, endpoint="analysis", event="schema_fail")
            logger.warning("llm_schema_failed endpoint=analysis user=%s error=%s", user_key, exc)
            raise ValueError("LLM analysis schema validation failed.") from exc

    def generate_chat_response(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.6,
        max_output_tokens: int = 400,
        user_id: int | None = None,
    ) -> str:
        user_key = f"user:{user_id}" if user_id is not None else "user:anonymous"
        return self._safe_llm_call(
            endpoint="chat",
            user_key=user_key,
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            temperature=temperature,
            max_output_tokens=max_output_tokens,
            expect_json=False,
        )

    def generate_employability_score(self, profile: StudentProfile) -> dict[str, Any]:
        user_key = f"user:{profile.user_id}"
        system_prompt = (
            "You are a placement evaluator. "
            "Given a student profile, return strict JSON employability scoring with no markdown."
        )
        user_prompt = (
            "Student profile:\n"
            f"12th Percentage: {profile.twelfth_percentage}\n"
            f"CGPA: {profile.cgpa}\n"
            f"Skills: {', '.join(profile.current_skills)}\n"
            f"Projects: {profile.projects}\n"
            f"Internships: {profile.internships}\n"
            f"Certifications: {profile.certifications}\n"
            f"Specialization: {profile.specialization}\n"
            "Required JSON format:\n"
            "{\n"
            '  "overall_score": 74,\n'
            '  "academic_strength": 78,\n'
            '  "technical_skills": 72,\n'
            '  "industry_readiness": 68,\n'
            '  "resume_quality": 71\n'
            "}\n"
        )

        raw_text = self._safe_llm_call(
            endpoint="analysis",
            user_key=user_key,
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            temperature=0.3,
            max_output_tokens=220,
            expect_json=True,
        )
        data = self._repair_json_if_needed(
            endpoint="analysis",
            user_key=user_key,
            raw_text=raw_text,
        )
        try:
            return EmployabilityScoreLLMOutput.model_validate(data).model_dump()
        except ValidationError as exc:
            record_llm_event(user_key=user_key, endpoint="analysis", event="schema_fail")
            logger.warning("llm_schema_failed endpoint=analysis user=%s error=%s", user_key, exc)
            raise ValueError("Invalid employability score schema") from exc

    def generate_psychometric_question(
        self,
        *,
        user_key: str,
        session_id: str,
        user_type: str,
        traits: dict[str, float],
        answers_summary: list[dict[str, Any]],
        schema_version: str,
        prompt_version: str,
    ) -> dict[str, Any]:
        system_prompt = (
            "You generate one adaptive psychometric multiple-choice question. "
            "Return strict JSON only. Avoid markdown. "
            "Each option must include trait_effect map with small bounded deltas."
        )
        user_prompt = (
            "Generate ONE psychometric question.\n"
            f"user_type: {user_type}\n"
            f"schema_version: {schema_version}\n"
            f"prompt_version: {prompt_version}\n"
            f"current_traits: {json.dumps(traits, ensure_ascii=True)}\n"
            f"recent_answers: {json.dumps(answers_summary[-3:], ensure_ascii=True)}\n"
            "Constraints:\n"
            "- question <= 15 words preferred\n"
            "- options: 3 or 4\n"
            "- each option has option_id,text,trait_effect\n"
            "- trait_effect deltas must remain within -0.35..0.35\n"
            "Output JSON format:\n"
            "{\n"
            '  "question": "...",\n'
            '  "trait_tag": "analytical",\n'
            '  "options": [\n'
            '    {"option_id": "a", "text": "...", "trait_effect": {"analytical": 0.12}}\n'
            "  ]\n"
            "}"
        )

        raw_text = self._safe_llm_call(
            endpoint="quiz_generation",
            user_key=user_key,
            usage_scope=f"quiz_session:{session_id}",
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            temperature=0.5,
            max_output_tokens=260,
            expect_json=True,
        )
        data = self._repair_json_if_needed(
            endpoint="quiz_generation",
            user_key=user_key,
            raw_text=raw_text,
        )
        try:
            validated = PsychometricQuestionLLMOutput.model_validate(data)
            return validated.model_dump()
        except ValidationError as exc:
            record_llm_event(user_key=user_key, endpoint="quiz_generation", event="schema_fail")
            logger.warning(
                "llm_schema_failed endpoint=quiz_generation user=%s error=%s",
                user_key,
                exc,
            )
            raise ValueError("Invalid psychometric question schema") from exc

    def generate_company_fit_matches(self, profile: StudentProfile) -> list[dict[str, Any]]:
        user_key = f"user:{profile.user_id}"
        system_prompt = (
            "You are a campus placement intelligence agent for Indian engineering colleges. "
            "Use common recruiter patterns and the student's evidence to produce company-specific readiness. "
            "Do not claim live openings or guaranteed placement. Return ONLY strict JSON."
        )
        user_prompt = (
            "Student profile:\n"
            f"Degree: {profile.degree}\n"
            f"Specialization: {profile.specialization}\n"
            f"CGPA: {profile.cgpa}\n"
            f"Skills: {', '.join(profile.current_skills)}\n"
            f"Projects: {profile.projects}\n"
            f"Internships: {profile.internships}\n"
            f"Certifications: {profile.certifications}\n"
            f"Target Industry: {profile.target_industry}\n"
            "Evaluate a balanced recruiter set relevant to the profile, such as Indian IT services, product engineering, analytics, cloud/SaaS, startups, and core domain employers. "
            "For each company, explain exactly what evidence matched and what is blocking readiness.\n"
            "Required JSON format:\n"
            "{\n"
            '  "matches": [\n'
            "    {\n"
            '      "company": "TCS Digital",\n'
            '      "company_type": "IT services / digital engineering",\n'
            '      "target_roles": ["Digital Software Engineer", "Data Engineer Trainee"],\n'
            '      "score": 76,\n'
            '      "rationale": "Good programming base but needs stronger project proof.",\n'
            '      "matched_evidence": ["Python listed", "2 projects"],\n'
            '      "missing_requirements": ["SQL depth", "DSA interview practice"],\n'
            '      "preparation_plan": ["Build one database-backed API", "Practice 40 DSA problems"],\n'
            '      "hiring_signal_summary": "Shortlist only after project evidence and coding practice improve."\n'
            "    }\n"
            "  ]\n"
            "}\n"
        )

        raw_text = self._safe_llm_call(
            endpoint="analysis",
            user_key=user_key,
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            temperature=0.4,
            max_output_tokens=420,
            expect_json=True,
        )
        data = self._repair_json_if_needed(
            endpoint="analysis",
            user_key=user_key,
            raw_text=raw_text,
        )
        try:
            validated = CompanyFitLLMOutput.model_validate(data)
            return validated.model_dump()["matches"]
        except ValidationError as exc:
            record_llm_event(user_key=user_key, endpoint="analysis", event="schema_fail")
            logger.warning("llm_schema_failed endpoint=analysis user=%s error=%s", user_key, exc)
            raise ValueError("Invalid company fit schema") from exc

    def generate_role_gaps(self, profile: StudentProfile) -> list[dict[str, Any]]:
        user_key = f"user:{profile.user_id}"
        system_prompt = (
            "You are a role-readiness analyst for campus placements. "
            "Compare the student's current evidence against realistic role expectations. "
            "Return strict JSON with concrete proof-building tasks, not generic course advice."
        )
        user_prompt = (
            "Student profile:\n"
            f"Degree: {profile.degree}\n"
            f"Specialization: {profile.specialization}\n"
            f"Skills: {', '.join(profile.current_skills)}\n"
            f"Projects: {profile.projects}\n"
            f"Internships: {profile.internships}\n"
            "Required JSON format:\n"
            "{\n"
            '  "role_gaps": [\n'
            "    {\n"
            '      "role": "Backend Developer",\n'
            '      "missing_skills": ["System design", "API testing"],\n'
            '      "learning_plan": ["Revise HTTP, SQL, and authentication", "Ship one deployed API"],\n'
            '      "current_evidence": ["Python skill listed", "2 projects"],\n'
            '      "gap_reason": "The profile shows coding interest but not production API evidence.",\n'
            '      "next_project": "Build a role-based FastAPI app with database, tests, and deployment.",\n'
            '      "proof_to_build": ["GitHub README", "API test suite", "Live demo URL"],\n'
            '      "priority": "high"\n'
            "    }\n"
            "  ]\n"
            "}\n"
        )

        raw_text = self._safe_llm_call(
            endpoint="analysis",
            user_key=user_key,
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            temperature=0.4,
            max_output_tokens=650,
            expect_json=True,
        )
        data = self._repair_json_if_needed(
            endpoint="analysis",
            user_key=user_key,
            raw_text=raw_text,
        )
        try:
            validated = RoleGapAnalysisLLMOutput.model_validate(data)
            return validated.model_dump()["role_gaps"]
        except ValidationError as exc:
            record_llm_event(user_key=user_key, endpoint="analysis", event="schema_fail")
            logger.warning("llm_schema_failed endpoint=analysis user=%s error=%s", user_key, exc)
            raise ValueError("Invalid role-gap schema") from exc

    def generate_placement_risk(self, profile: StudentProfile) -> dict[str, Any]:
        user_key = f"user:{profile.user_id}"
        system_prompt = (
            "You are a placement risk assessor. "
            "Return strict JSON with risk_level and concise reasons only."
        )
        user_prompt = (
            "Student profile:\n"
            f"12th Percentage: {profile.twelfth_percentage}\n"
            f"CGPA: {profile.cgpa}\n"
            f"Skills Count: {len(profile.current_skills)}\n"
            f"Projects: {profile.projects}\n"
            f"Internships: {profile.internships}\n"
            f"Certifications: {profile.certifications}\n"
            "Required JSON format:\n"
            "{\n"
            '  "risk_level": "Medium",\n'
            '  "reasons": ["Limited internship exposure"]\n'
            "}\n"
        )

        raw_text = self._safe_llm_call(
            endpoint="analysis",
            user_key=user_key,
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            temperature=0.2,
            max_output_tokens=220,
            expect_json=True,
        )
        data = self._repair_json_if_needed(
            endpoint="analysis",
            user_key=user_key,
            raw_text=raw_text,
        )
        try:
            return PlacementRiskLLMOutput.model_validate(data).model_dump()
        except ValidationError as exc:
            record_llm_event(user_key=user_key, endpoint="analysis", event="schema_fail")
            logger.warning("llm_schema_failed endpoint=analysis user=%s error=%s", user_key, exc)
            raise ValueError("Invalid placement risk schema") from exc

    def generate_internship_readiness(self, profile: StudentProfile) -> dict[str, Any]:
        user_key = f"user:{profile.user_id}"
        system_prompt = (
            "You are an internship readiness evaluator. "
            "Return strict JSON with score, level, and concrete action_plan only. "
            "readiness_level must be exactly one of: Low, Medium, High."
        )
        user_prompt = (
            "Student profile:\n"
            f"CGPA: {profile.cgpa}\n"
            f"Skills: {', '.join(profile.current_skills)}\n"
            f"Projects: {profile.projects}\n"
            f"Internships: {profile.internships}\n"
            f"Certifications: {profile.certifications}\n"
            f"Specialization: {profile.specialization}\n"
            "Required JSON format:\n"
            "{\n"
            '  "readiness_score": 68,\n'
            '  "readiness_level": "Medium",\n'
            '  "action_plan": ["Build one industry-grade project", "Apply to 20 internships"]\n'
            "}\n"
        )

        raw_text = self._safe_llm_call(
            endpoint="analysis",
            user_key=user_key,
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            temperature=0.3,
            max_output_tokens=320,
            expect_json=True,
        )
        data = self._repair_json_if_needed(
            endpoint="analysis",
            user_key=user_key,
            raw_text=raw_text,
        )
        data = self._normalize_internship_readiness_payload(payload=data, user_key=user_key)
        try:
            return InternshipReadinessLLMOutput.model_validate(data).model_dump()
        except ValidationError as exc:
            record_llm_event(user_key=user_key, endpoint="analysis", event="schema_fail")
            logger.warning("llm_schema_failed endpoint=analysis user=%s error=%s", user_key, exc)
            raise ValueError("Invalid internship readiness schema") from exc

    def generate_resume_analysis(self, profile: StudentProfile, resume_text: str) -> dict[str, Any]:
        user_key = f"user:{profile.user_id}"
        system_prompt = (
            "You are an expert resume reviewer for campus placements. "
            "Return only strict JSON according to the required schema."
        )
        user_prompt = (
            "Student profile:\n"
            f"Degree: {profile.degree}\n"
            f"Specialization: {profile.specialization}\n"
            f"Target Industry: {profile.target_industry}\n"
            "Resume text:\n"
            f"{resume_text[:12000]}\n"
            "Required JSON format:\n"
            "{\n"
            '  "extracted_skills": ["Python", "SQL"],\n'
            '  "projects": ["Project title"],\n'
            '  "experience": ["Internship details"],\n'
            '  "education": ["B.Tech CSE"],\n'
            '  "resume_score": 72,\n'
            '  "missing_keywords": ["MLOps"],\n'
            '  "weak_sections": ["experience"],\n'
            '  "suggestions": ["Quantify project outcomes"]\n'
            "}\n"
        )

        raw_text = self._safe_llm_call(
            endpoint="analysis",
            user_key=user_key,
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            temperature=0.2,
            max_output_tokens=900,
            expect_json=True,
        )
        data = self._repair_json_if_needed(
            endpoint="analysis",
            user_key=user_key,
            raw_text=raw_text,
        )
        try:
            return ResumeAnalysisLLMOutput.model_validate(data).model_dump()
        except ValidationError as exc:
            record_llm_event(user_key=user_key, endpoint="analysis", event="schema_fail")
            logger.warning("llm_schema_failed endpoint=analysis user=%s error=%s", user_key, exc)
            raise ValueError("Invalid resume analysis schema") from exc

    def generate_training_recommendations(
        self,
        *,
        total_students: int,
        weak_skills: list[dict[str, Any]],
        user_id: int | None = None,
    ) -> list[dict[str, Any]]:
        user_key = f"user:{user_id}" if user_id is not None else "user:system"
        system_prompt = (
            "You are a training program designer for placement cells. "
            "Given weak-skill statistics, return practical training programs as strict JSON."
        )
        user_prompt = (
            f"Total students: {total_students}\n"
            f"Weak skill stats: {json.dumps(weak_skills)}\n"
            "Required JSON format:\n"
            "{\n"
            '  "programs": [\n'
            '    {"title": "ML Foundations", "focus_skills": ["Machine Learning", "Python"], "description": "8-week intensive"}\n'
            "  ]\n"
            "}\n"
        )

        raw_text = self._safe_llm_call(
            endpoint="analysis",
            user_key=user_key,
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            temperature=0.3,
            max_output_tokens=500,
            expect_json=True,
        )
        data = self._repair_json_if_needed(
            endpoint="analysis",
            user_key=user_key,
            raw_text=raw_text,
        )
        try:
            validated = TrainingRecommendationsLLMOutput.model_validate(data)
            return validated.model_dump()["programs"]
        except ValidationError as exc:
            record_llm_event(user_key=user_key, endpoint="analysis", event="schema_fail")
            logger.warning("llm_schema_failed endpoint=analysis user=%s error=%s", user_key, exc)
            raise ValueError("Invalid training recommendations schema") from exc

    def generate_employability_adjustments(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.3,
        max_output_tokens: int = 300,
        user_id: int | None = None,
    ) -> dict[str, Any]:
        user_key = f"user:{user_id}" if user_id is not None else "user:anonymous"
        raw_text = self._safe_llm_call(
            endpoint="analysis",
            user_key=user_key,
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            temperature=temperature,
            max_output_tokens=max_output_tokens,
            expect_json=True,
        )
        data = self._repair_json_if_needed(
            endpoint="analysis",
            user_key=user_key,
            raw_text=raw_text,
        )
        try:
            return EmployabilityAdjustments.model_validate(data).model_dump()
        except ValidationError as exc:
            record_llm_event(user_key=user_key, endpoint="analysis", event="schema_fail")
            logger.warning("llm_schema_failed endpoint=analysis user=%s error=%s", user_key, exc)
            raise ValueError("Invalid employability adjustment schema") from exc

    def generate_company_fit_adjustments(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.4,
        max_output_tokens: int = 200,
        user_id: int | None = None,
    ) -> dict[str, int]:
        user_key = f"user:{user_id}" if user_id is not None else "user:anonymous"
        raw_text = self._safe_llm_call(
            endpoint="analysis",
            user_key=user_key,
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            temperature=temperature,
            max_output_tokens=max_output_tokens,
            expect_json=True,
        )
        data = self._repair_json_if_needed(
            endpoint="analysis",
            user_key=user_key,
            raw_text=raw_text,
        )
        try:
            return CompanyFitAdjustments.model_validate(data).root
        except ValidationError as exc:
            record_llm_event(user_key=user_key, endpoint="analysis", event="schema_fail")
            logger.warning("llm_schema_failed endpoint=analysis user=%s error=%s", user_key, exc)
            raise ValueError("Invalid company fit adjustment schema") from exc

    def generate_industry_trends(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.5,
        max_output_tokens: int = 200,
        user_id: int | None = None,
    ) -> dict[str, Any]:
        user_key = f"user:{user_id}" if user_id is not None else "user:anonymous"
        raw_text = self._safe_llm_call(
            endpoint="industry",
            user_key=user_key,
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            temperature=temperature,
            max_output_tokens=max_output_tokens,
            expect_json=True,
        )
        data = self._repair_json_if_needed(
            endpoint="industry",
            user_key=user_key,
            raw_text=raw_text,
        )
        try:
            return IndustryTrendsOutput.model_validate(data).model_dump()
        except ValidationError as exc:
            record_llm_event(user_key=user_key, endpoint="industry", event="schema_fail")
            logger.warning("llm_schema_failed endpoint=industry user=%s error=%s", user_key, exc)
            raise ValueError("Invalid industry trends schema") from exc

    def generate_program_fit_analysis(
        self,
        profile: StudentProfile,
        program_options: list[dict[str, Any]],
        catalog_version: str,
        rag_context: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        user_key = f"user:{profile.user_id}"
        subjects_str = ", ".join(profile.subjects) if profile.subjects else "Not specified"
        bounded_program_options = self._canonicalize_program_options(program_options)
        bounded_rag_context = [
            {
                "source_title": item.get("source_title"),
                "source_type": item.get("source_type"),
                "excerpt": item.get("excerpt"),
            }
            for item in (rag_context or [])[:5]
            if item.get("source_title") and item.get("excerpt")
        ]
        allowed_program_ids = {
            option["program_id"]
            for option in bounded_program_options
            if isinstance(option.get("program_id"), str)
        }
        if not allowed_program_ids:
            raise ValueError("At least one configured program option is required.")
        settings = getattr(self, "_settings", get_settings())
        branding = BRANDING_BY_MODE[getattr(settings, "institution_mode", "sage")]
        sample_program = bounded_program_options[0]
        sample_program_id = sample_program.get("program_id") or "configured-program"
        sample_program_name = sample_program.get("program_name") or "Configured Program"
        sample_school = (
            sample_program.get("school")
            or branding.institution_short_name
        )
        institution_context = branding.institution_short_name
        program_options_json = json.dumps(bounded_program_options, ensure_ascii=False)
        rag_context_json = json.dumps(bounded_rag_context, ensure_ascii=False)
        system_prompt = (
            f"You are an institutional career counselor for {institution_context} admissions "
            f"inside {branding.product_name}. "
            "Use the provided configured programs only. Return ONLY valid JSON matching the schema. "
            "Be honest about expectation-versus-reality gaps and first-year effort. "
            "Write expectation checks like a counselor speaking from the student's actual "
            "interests, subjects, skills, and preferred program, not as generic examples."
        )
        user_prompt = (
            f"Analyze this student's fit across configured {institution_context} programs.\n"
            f"Catalog version: {catalog_version}\n"
            f"Program options JSON: {program_options_json}\n"
            f"Retrieved institution evidence JSON: {rag_context_json}\n"
            f"Name: {profile.name}\n"
            f"12th Percentage: {profile.twelfth_percentage}%\n"
            f"Subjects Studied: {subjects_str}\n"
            f"Math Strength: {profile.math_strength or 'Not specified'}\n"
            f"Logical Reasoning: {profile.logical_reasoning or 'Not specified'}\n"
            f"Programming Interest: {profile.programming_interest or 'Not specified'}\n"
            f"Interests: {', '.join(profile.interests)}\n"
            f"Current Skills: {', '.join(profile.current_skills)}\n"
            f"Degree Interest: {profile.degree}\n"
            f"Specialization Interest: {profile.specialization}\n"
            "\n"
            "Required JSON format:\n"
            "{\n"
            f'  "program_fit_summary": {{"recommended_program_id": "{sample_program_id}", '
            f'"recommended_program_name": "{sample_program_name}", "confidence": 86, '
            '"summary": "Strong fit for programming, mathematics, and AI goals."},\n'
            f'  "program_recommendations": [{{"program_id": "{sample_program_id}", '
            f'"program_name": "{sample_program_name}", "school": "{sample_school}", '
            '"fit_score": 86, "fit_level": "High", "reasons": ["Strong mathematics"], '
            '"career_paths": ["Machine Learning Engineer"], "priority_skills": ["Python"], '
            '"first_year_focus": ["Python foundations"]}],\n'
            '  "expectation_reality_checks": [{"expectation": "Student expects their '
            'AI tools interest to become advanced project work quickly", '
            '"reality": "The first year still needs Python, mathematics, and data '
            'handling evidence.", "counselor_note": "Set a weekly practice plan '
            'and one proof-of-work project."}],\n'
            '  "first_year_roadmap": [{"term": "Semester 1", '
            '"focus": ["Programming fundamentals"], "evidence_to_build": ["Mini project"]}],\n'
            '  "counselor_summary": {"best_fit": "B.Tech CSE - AIML", '
            '"risk_flags": ["May underestimate mathematics"], '
            '"talking_points": ["Discuss daily coding practice"], '
            '"follow_up_questions": ["Can you practice coding daily?"]}\n'
            "}\n"
        )

        raw_text = self._safe_llm_call(
            endpoint="program_fit",
            user_key=user_key,
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            temperature=0.5,
            max_output_tokens=1200,
            expect_json=True,
        )
        data = self._repair_json_if_needed(
            endpoint="program_fit",
            user_key=user_key,
            raw_text=raw_text,
        )
        try:
            validated = ProgramFitLLMOutput.model_validate(data)
            result = validated.model_dump()
            self._validate_program_fit_ids(
                result,
                allowed_program_ids=allowed_program_ids,
                user_key=user_key,
            )
            return result
        except ValidationError as exc:
            record_llm_event(user_key=user_key, endpoint="program_fit", event="schema_fail")
            logger.warning(
                "llm_schema_failed endpoint=program_fit user=%s error=%s",
                user_key,
                exc,
            )
            raise ValueError("LLM program fit schema validation failed.") from exc

    def _canonicalize_program_options(
        self,
        program_options: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        allowed_fields = (
            "program_id",
            "program_name",
            "school",
            "priority_skills",
            "career_paths",
            "admission_fit_signals",
            "reality_checks",
        )
        canonical_options: list[dict[str, Any]] = []
        for option in program_options:
            if option.get("is_active") is False:
                continue
            canonical = {
                field: option[field]
                for field in allowed_fields
                if field in option and option[field] is not None
            }
            if canonical.get("program_id"):
                canonical_options.append(canonical)
            if len(canonical_options) >= 12:
                break
        return canonical_options

    def _validate_program_fit_ids(
        self,
        result: dict[str, Any],
        *,
        allowed_program_ids: set[str],
        user_key: str,
    ) -> None:
        recommendations = result.get("program_recommendations", [])
        recommended_ids = {
            item.get("program_id")
            for item in recommendations
            if isinstance(item, dict) and isinstance(item.get("program_id"), str)
        }
        summary = result.get("program_fit_summary", {})
        summary_program_id = summary.get("recommended_program_id") if isinstance(summary, dict) else None

        has_unknown_recommendation = not recommended_ids.issubset(allowed_program_ids)
        has_unknown_summary = summary_program_id not in allowed_program_ids
        summary_missing_from_recommendations = summary_program_id not in recommended_ids

        if (
            has_unknown_recommendation
            or has_unknown_summary
            or summary_missing_from_recommendations
        ):
            record_llm_event(user_key=user_key, endpoint="program_fit", event="schema_fail")
            logger.warning(
                "llm_schema_failed endpoint=program_fit user=%s error=unknown_program_id",
                user_key,
            )
            raise ValueError("LLM program fit referenced unknown configured program.")

    def generate_branch_analysis(self, profile: StudentProfile) -> dict[str, Any]:
        user_key = f"user:{profile.user_id}"

        subjects_str = ", ".join(profile.subjects) if profile.subjects else "Not specified"
        system_prompt = (
            "You are an expert career advisor for 12th-grade students choosing engineering branches. "
            "Analyze the student's profile and compare two engineering branches: "
            "Artificial Intelligence and Machine Learning versus Cyber Security. "
            "Return ONLY valid JSON that matches the required schema."
        )
        user_prompt = (
            "Analyze the following student profile for branch compatibility between AIML and Cyber Security.\n"
            f"Name: {profile.name}\n"
            f"12th Percentage: {profile.twelfth_percentage}%\n"
            f"Subjects Studied: {subjects_str}\n"
            f"Math Strength: {profile.math_strength or 'Not specified'}\n"
            f"Logical Reasoning: {profile.logical_reasoning or 'Not specified'}\n"
            f"Programming Interest: {profile.programming_interest or 'Not specified'}\n"
            f"Interests: {', '.join(profile.interests)}\n"
            f"Current Skills: {', '.join(profile.current_skills)}\n"
            f"Degree: {profile.degree}\n"
            f"Specialization: {profile.specialization}\n"
            "\n"
            "Required JSON format:\n"
            "{\n"
            '  "aiml_score": 86,\n'
            '  "cyber_security_score": 74,\n'
            '  "recommended_branch": "AIML",\n'
            '  "branch_reasoning": [{"reason": "Strong mathematics foundation"}],\n'
            '  "aiml_roles": [{"role": "Machine Learning Engineer", "score": 90}],\n'
            '  "cyber_roles": [{"role": "Security Analyst", "score": 70}],\n'
            '  "aiml_skills": ["Python", "Linear Algebra"],\n'
            '  "cyber_skills": ["Computer Networking", "Linux"],\n'
            '  "aiml_roadmap": [{"year": 1, "topics": ["Python"]}],\n'
            '  "cyber_roadmap": [{"year": 1, "topics": ["Networking"]}],\n'
            '  "industry_insights": [{"branch": "AIML", "insight": "Rapid growth due to AI adoption"}]\n'
            "}\n"
        )

        raw_text = self._safe_llm_call(
            endpoint="analysis",
            user_key=user_key,
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            temperature=0.6,
            max_output_tokens=900,
            expect_json=True,
        )
        data = self._repair_json_if_needed(
            endpoint="analysis",
            user_key=user_key,
            raw_text=raw_text,
        )
        try:
            validated = BranchAnalysisLLMOutput.model_validate(data)
            return validated.model_dump()
        except ValidationError as exc:
            record_llm_event(user_key=user_key, endpoint="analysis", event="schema_fail")
            logger.warning("llm_schema_failed endpoint=analysis user=%s error=%s", user_key, exc)
            raise ValueError("LLM branch analysis schema validation failed.") from exc
