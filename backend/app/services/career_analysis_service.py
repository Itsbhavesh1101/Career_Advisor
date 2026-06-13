from __future__ import annotations

import logging
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.student_profile import StudentProfile
from app.models.career_analysis import CareerAnalysis
from app.schemas.career_analysis import CareerAnalysisCreate
from app.services.ai_engine import CareerAIEngine
from app.services.institution_config_service import InstitutionConfigService
from app.services.rag_service import RAGService


logger = logging.getLogger(__name__)


def _legacy_branch_fields_from_program_fit(
    program_fit: dict | None,
) -> dict[str, object | None]:
    empty_fields: dict[str, object | None] = {
        "aiml_score": None,
        "cyber_security_score": None,
        "recommended_branch": None,
        "branch_reasoning": None,
        "aiml_roles": None,
        "cyber_roles": None,
        "aiml_skills": None,
        "cyber_skills": None,
        "aiml_roadmap": None,
        "cyber_roadmap": None,
        "industry_insights": None,
    }
    if not program_fit:
        return empty_fields

    recommendations = program_fit.get("program_recommendations") or []
    if not isinstance(recommendations, list):
        return empty_fields

    def _program_id(item: Any) -> str:
        return item.get("program_id", "").lower() if isinstance(item, dict) else ""

    def _legacy_branch_label(item: Any) -> str | None:
        if not isinstance(item, dict):
            return None
        program_id = str(item.get("program_id") or "").lower()
        program_name = str(item.get("program_name") or "").lower()
        legacy_key = f"{program_id} {program_name}"
        if "aiml" in legacy_key:
            return "AIML"
        if "cyber" in legacy_key:
            return "Cyber Security"
        return item.get("program_name")

    aiml = next(
        (item for item in recommendations if "aiml" in _program_id(item)),
        None,
    )
    cyber = next(
        (item for item in recommendations if "cyber" in _program_id(item)),
        None,
    )
    summary = program_fit.get("program_fit_summary") or {}
    if not isinstance(summary, dict):
        summary = {}
    summary_legacy_label = _legacy_branch_label(
        {
            "program_id": summary.get("recommended_program_id"),
            "program_name": summary.get("recommended_program_name"),
        }
    )
    summary_program_id = str(summary.get("recommended_program_id") or "").lower()
    summary_program_name = str(summary.get("recommended_program_name") or "").lower()

    def _matches_summary(item: Any) -> bool:
        if not isinstance(item, dict):
            return False
        program_id = str(item.get("program_id") or "").lower()
        program_name = str(item.get("program_name") or "").lower()
        return bool(
            (summary_program_id and program_id == summary_program_id)
            or (summary_program_name and program_name == summary_program_name)
        )

    summary_match = next(
        (item for item in recommendations if _matches_summary(item)),
        None,
    )

    fallback_program = recommendations[0] if recommendations else {}
    leading_program = summary_match or aiml or cyber or fallback_program
    reasons = (
        leading_program.get("reasons", [])
        if isinstance(leading_program, dict)
        else []
    )

    return {
        "aiml_score": aiml.get("fit_score") if isinstance(aiml, dict) else None,
        "cyber_security_score": cyber.get("fit_score") if isinstance(cyber, dict) else None,
        "recommended_branch": summary_legacy_label,
        "branch_reasoning": [{"reason": reason} for reason in reasons] or None,
        "aiml_roles": [
            {"role": role, "score": aiml.get("fit_score", 0)}
            for role in (aiml or {}).get("career_paths", [])
        ]
        or None,
        "cyber_roles": [
            {"role": role, "score": cyber.get("fit_score", 0)}
            for role in (cyber or {}).get("career_paths", [])
        ]
        or None,
        "aiml_skills": (aiml or {}).get("priority_skills"),
        "cyber_skills": (cyber or {}).get("priority_skills"),
        "aiml_roadmap": [{"year": 1, "topics": aiml.get("first_year_focus", [])}]
        if isinstance(aiml, dict)
        else None,
        "cyber_roadmap": [{"year": 1, "topics": cyber.get("first_year_focus", [])}]
        if isinstance(cyber, dict)
        else None,
        "industry_insights": [
            {
                "branch": _legacy_branch_label(item),
                "insight": "; ".join(item.get("career_paths", [])[:3]),
            }
            for item in recommendations
            if isinstance(item, dict)
        ]
        or None,
    }


def _text_tokens(*values: object) -> set[str]:
    text = " ".join(str(value or "") for value in values).lower()
    for char in ",;:/()[]{}-_":
        text = text.replace(char, " ")
    return {token for token in text.split() if len(token) >= 3}


def _program_fit_level(score: int) -> str:
    if score >= 78:
        return "High"
    if score >= 58:
        return "Medium"
    return "Low"


def _catalog_program_fallback(
    *,
    program: dict,
    profile: StudentProfile,
    existing_scores: list[int],
    fallback_school: str = "SAGE/SIRT",
) -> dict:
    profile_tokens = _text_tokens(
        getattr(profile, "degree", None),
        getattr(profile, "specialization", None),
        " ".join(getattr(profile, "subjects", None) or []),
        " ".join(getattr(profile, "interests", None) or []),
        " ".join(getattr(profile, "current_skills", None) or []),
        getattr(profile, "math_strength", None),
        getattr(profile, "logical_reasoning", None),
        getattr(profile, "programming_interest", None),
    )
    program_tokens = _text_tokens(
        program.get("program_name"),
        " ".join(program.get("priority_skills") or []),
        " ".join(program.get("career_paths") or []),
        " ".join(program.get("admission_fit_signals") or []),
    )
    overlap = profile_tokens.intersection(program_tokens)
    base_score = 52 + min(len(overlap) * 6, 30)
    if existing_scores:
        base_score = min(base_score, max(max(existing_scores) - 8, 45))
    fit_score = max(35, min(base_score, 88))

    reasons = [
        f"Catalog comparison included because {program.get('program_name')} is an active option.",
    ]
    if overlap:
        reasons.append(
            "Profile overlap: " + ", ".join(sorted(overlap)[:5]) + "."
        )
    else:
        reasons.append(
            "Needs counselor discussion because the profile does not strongly signal this program yet."
        )
    for signal in (program.get("admission_fit_signals") or [])[:2]:
        reasons.append(f"Fit signal to verify: {signal}.")

    return {
        "program_id": program["program_id"],
        "program_name": program["program_name"],
        "school": program.get("school") or fallback_school,
        "fit_score": fit_score,
        "fit_level": _program_fit_level(fit_score),
        "reasons": reasons[:4],
        "career_paths": (program.get("career_paths") or ["Counselor mapped pathway"])[:6],
        "priority_skills": (program.get("priority_skills") or ["Foundation readiness"])[:8],
        "first_year_focus": (
            program.get("priority_skills")
            or program.get("admission_fit_signals")
            or ["Build first-semester evidence"]
        )[:6],
    }


def _ensure_program_recommendation_coverage(
    program_fit: dict | None,
    program_options: list[dict],
    profile: StudentProfile,
    fallback_school: str = "SAGE/SIRT",
) -> dict | None:
    if not program_fit:
        return None

    recommendations = program_fit.get("program_recommendations")
    if not isinstance(recommendations, list):
        recommendations = []

    covered_ids = {
        item.get("program_id")
        for item in recommendations
        if isinstance(item, dict) and item.get("program_id")
    }
    existing_scores = [
        int(item.get("fit_score"))
        for item in recommendations
        if isinstance(item, dict) and isinstance(item.get("fit_score"), int)
    ]
    enriched = [item for item in recommendations if isinstance(item, dict)]

    for program in program_options:
        program_id = program.get("program_id")
        if not program_id or program_id in covered_ids:
            continue
        enriched.append(
            _catalog_program_fallback(
                program=program,
                profile=profile,
                existing_scores=existing_scores,
                fallback_school=fallback_school,
            )
        )
        covered_ids.add(program_id)

    program_fit = dict(program_fit)
    program_fit["program_recommendations"] = enriched
    return program_fit


def _string_items(value: object) -> list[str]:
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    if isinstance(value, tuple):
        return [str(item).strip() for item in value if str(item).strip()]
    if isinstance(value, str) and value.strip():
        return [value.strip()]
    return []


def _compact_label(values: list[str], fallback: str, *, limit: int = 3) -> str:
    cleaned = [value for value in values if value]
    if not cleaned:
        return fallback
    return ", ".join(cleaned[:limit])


def _program_by_id(program_options: list[dict]) -> dict[str, dict]:
    return {
        str(program.get("program_id")): program
        for program in program_options
        if program.get("program_id")
    }


def _leading_program_context(
    program_fit: dict,
    program_options: list[dict],
) -> tuple[dict, dict]:
    recommendations = program_fit.get("program_recommendations")
    if not isinstance(recommendations, list):
        recommendations = []
    summary = program_fit.get("program_fit_summary")
    if not isinstance(summary, dict):
        summary = {}
    summary_program_id = str(summary.get("recommended_program_id") or "")
    catalog_by_id = _program_by_id(program_options)
    recommendation = next(
        (
            item
            for item in recommendations
            if isinstance(item, dict)
            and str(item.get("program_id") or "") == summary_program_id
        ),
        None,
    )
    if not isinstance(recommendation, dict):
        recommendation = next(
            (item for item in recommendations if isinstance(item, dict)),
            {},
        )
    catalog_program = catalog_by_id.get(
        str(recommendation.get("program_id") or summary_program_id),
        {},
    )
    return recommendation, catalog_program


def _is_generic_expectation_check(item: object) -> bool:
    if not isinstance(item, dict):
        return True
    text = " ".join(
        str(item.get(field) or "")
        for field in ("expectation", "student_expectation", "reality", "reality_check", "counselor_note")
    ).lower()
    generic_fragments = (
        "ai starts with model building",
        "only model training",
        "first year focuses on programming and mathematics",
        "explain the foundation path",
    )
    return any(fragment in text for fragment in generic_fragments)


def _personalized_expectation_reality_checks(
    *,
    profile: StudentProfile,
    recommendation: dict,
    catalog_program: dict,
) -> list[dict[str, str]]:
    program_name = (
        str(recommendation.get("program_name") or catalog_program.get("program_name") or "")
        or "the recommended program"
    )
    interests = _string_items(getattr(profile, "interests", None))
    subjects = _string_items(getattr(profile, "subjects", None))
    current_skills = _string_items(getattr(profile, "current_skills", None))
    priority_skills = _string_items(
        recommendation.get("priority_skills") or catalog_program.get("priority_skills")
    )
    career_paths = _string_items(
        recommendation.get("career_paths") or catalog_program.get("career_paths")
    )
    reality_checks = _string_items(catalog_program.get("reality_checks"))
    fit_reasons = _string_items(recommendation.get("reasons"))

    interest_label = _compact_label(interests, "this career direction")
    subject_label = _compact_label(subjects, "your current subjects")
    current_skill_label = _compact_label(current_skills, "your current strengths")
    priority_skill_label = _compact_label(priority_skills, "foundation skills")
    career_label = _compact_label(career_paths, "target roles")
    reality_label = (
        reality_checks[0]
        if reality_checks
        else f"{program_name} requires steady foundation practice before advanced work."
    )
    fit_reason = (
        fit_reasons[0]
        if fit_reasons
        else "The current profile shows enough signal to start a structured fit discussion."
    )

    checks = [
        {
            "expectation": (
                f"You are expecting {interest_label} to connect quickly with "
                f"{program_name} outcomes."
            ),
            "reality": (
                f"{program_name} still needs visible evidence in {priority_skill_label}. "
                f"{reality_label}"
            ),
            "counselor_note": (
                "Counselor advice: keep the interest, but convert it into a weekly "
                "practice plan and one small proof-of-work project."
            ),
        },
        {
            "expectation": (
                f"Because {subject_label} and {current_skill_label} are present, the fit may "
                "feel already decided."
            ),
            "reality": (
                f"{fit_reason} The next counseling step is to verify effort habits, "
                f"math/programming comfort, and readiness for {priority_skill_label}."
            ),
            "counselor_note": (
                "Counselor advice: discuss the first semester workload honestly before "
                "treating the recommendation as final."
            ),
        },
        {
            "expectation": f"The preferred outcome may be roles like {career_label}.",
            "reality": (
                f"Those roles become realistic only after the student builds semester-wise "
                f"evidence in {priority_skill_label}, not only after choosing the branch."
            ),
            "counselor_note": (
                "Counselor advice: set a 30-day starter action and review progress before "
                "the next admission or parent discussion."
            ),
        },
    ]
    return checks


def _ensure_personalized_expectation_reality_checks(
    program_fit: dict | None,
    *,
    profile: StudentProfile,
    program_options: list[dict],
) -> dict | None:
    if not program_fit:
        return None
    recommendation, catalog_program = _leading_program_context(
        program_fit,
        program_options,
    )
    personalized = _personalized_expectation_reality_checks(
        profile=profile,
        recommendation=recommendation,
        catalog_program=catalog_program,
    )
    existing = program_fit.get("expectation_reality_checks")
    existing_items = existing if isinstance(existing, list) else []
    useful_existing = [
        item
        for item in existing_items
        if isinstance(item, dict) and not _is_generic_expectation_check(item)
    ]
    merged = [*personalized[:2], *useful_existing, personalized[2]]
    program_fit = dict(program_fit)
    program_fit["expectation_reality_checks"] = merged[:3]
    return program_fit


class CareerAnalysisService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create_analysis(
        self, profile_id: int, payload: CareerAnalysisCreate
    ) -> CareerAnalysis:
        analysis = CareerAnalysis(
            student_profile_id=profile_id,
            career_recommendations=payload.career_recommendations,
            skill_gaps=payload.skill_gaps,
            learning_roadmap=payload.learning_roadmap,
            salary_insights=payload.salary_insights,
            industry_trends=payload.industry_trends,
            institution_config_version=payload.institution_config_version,
            program_fit_summary=payload.program_fit_summary,
            program_recommendations=payload.program_recommendations,
            expectation_reality_checks=payload.expectation_reality_checks,
            first_year_roadmap=payload.first_year_roadmap,
            counselor_summary=payload.counselor_summary,
            rag_evidence=payload.rag_evidence,
            aiml_score=payload.aiml_score,
            cyber_security_score=payload.cyber_security_score,
            recommended_branch=payload.recommended_branch,
            branch_reasoning=payload.branch_reasoning,
            aiml_roles=payload.aiml_roles,
            cyber_roles=payload.cyber_roles,
            aiml_skills=payload.aiml_skills,
            cyber_skills=payload.cyber_skills,
            aiml_roadmap=payload.aiml_roadmap,
            cyber_roadmap=payload.cyber_roadmap,
            industry_insights=payload.industry_insights,
        )
        self.db.add(analysis)
        self.db.commit()
        self.db.refresh(analysis)
        return analysis

    def get_analysis_by_profile_id(
        self, profile_id: int, user_id: int, allow_admin: bool = False
    ) -> CareerAnalysis | None:
        stmt = (
            select(CareerAnalysis)
            .where(CareerAnalysis.student_profile_id == profile_id)
            .order_by(CareerAnalysis.created_at.desc())
        )
        analysis = self.db.scalar(stmt)
        if analysis is None:
            return None
        if not allow_admin:
            profile = self.db.get(StudentProfile, profile_id)
            if profile is None or profile.user_id != user_id:
                return None
        return analysis

    def generate_analysis(
        self, profile_id: int, user_id: int, allow_admin: bool = False
    ) -> CareerAnalysis:
        profile = self.db.get(StudentProfile, profile_id)
        if profile is None or (profile.user_id != user_id and not allow_admin):
            raise ValueError("Profile not found")

        user_type = profile.user_type or "college_student"
        is_twelfth_student = user_type == "twelfth_student"

        engine = CareerAIEngine()

        program_fit = None
        rag_evidence = None
        institution_config_version = None
        branch_analysis_source = "not_applicable"

        if is_twelfth_student:
            institution_service = InstitutionConfigService(self.db)
            fallback_school = "SAGE/SIRT"
            if hasattr(institution_service, "get_branding"):
                fallback_school = institution_service.get_branding().institution_short_name
            catalog = institution_service.get_catalog()
            program_options = [
                {
                    "program_id": program.program_id,
                    "program_name": program.program_name,
                    "school": school.school_name,
                    "priority_skills": program.priority_skills,
                    "career_paths": program.career_paths,
                    "admission_fit_signals": program.admission_fit_signals,
                    "reality_checks": program.reality_checks,
                }
                for school in catalog.schools
                for program in school.programs
                if school.is_active and program.is_active
            ]
            if program_options:
                rag_query = " ".join(
                    [
                        getattr(profile, "degree", None) or "",
                        getattr(profile, "specialization", None) or "",
                        " ".join(getattr(profile, "subjects", None) or []),
                        " ".join(getattr(profile, "interests", None) or []),
                        " ".join(getattr(profile, "current_skills", None) or []),
                        " ".join(program["program_name"] for program in program_options),
                    ]
                )
                rag_evidence = []
                try:
                    rag_evidence = [
                        item.model_dump()
                        for item in RAGService(self.db).search(
                            rag_query,
                            program_ids=[
                                program["program_id"] for program in program_options
                            ],
                            limit=5,
                        )
                    ]
                except Exception as exc:
                    logger.warning(
                        "rag_retrieval_failed profile_id=%s user_id=%s error=%s",
                        profile_id,
                        user_id,
                        exc,
                    )
                program_fit = engine.generate_program_fit_analysis(
                    profile,
                    program_options,
                    catalog.version,
                    rag_context=rag_evidence,
                )
                program_fit = _ensure_program_recommendation_coverage(
                    program_fit,
                    program_options,
                    profile,
                    fallback_school=fallback_school,
                )
                program_fit = _ensure_personalized_expectation_reality_checks(
                    program_fit,
                    profile=profile,
                    program_options=program_options,
                )
                institution_config_version = catalog.version
                branch_analysis_source = getattr(
                    engine,
                    "program_fit_analysis_source",
                    getattr(engine, "branch_analysis_source", "unknown"),
                )
            else:
                branch_analysis_source = "catalog_unavailable"
            legacy_fields = _legacy_branch_fields_from_program_fit(program_fit)
        else:
            legacy_fields = _legacy_branch_fields_from_program_fit(None)

        payload = CareerAnalysisCreate(
            career_recommendations=engine.generate_career_recommendations(profile),
            skill_gaps=engine.generate_skill_gaps(profile),
            learning_roadmap=engine.generate_learning_roadmap(profile),
            salary_insights=engine.generate_salary_insights(profile),
            industry_trends=engine.generate_industry_trends(profile),
            institution_config_version=institution_config_version,
            program_fit_summary=(program_fit or {}).get("program_fit_summary"),
            program_recommendations=(program_fit or {}).get("program_recommendations"),
            expectation_reality_checks=(program_fit or {}).get(
                "expectation_reality_checks"
            ),
            first_year_roadmap=(program_fit or {}).get("first_year_roadmap"),
            counselor_summary=(program_fit or {}).get("counselor_summary"),
            rag_evidence=rag_evidence,
            aiml_score=legacy_fields["aiml_score"],
            cyber_security_score=legacy_fields["cyber_security_score"],
            recommended_branch=legacy_fields["recommended_branch"],
            branch_reasoning=legacy_fields["branch_reasoning"],
            aiml_roles=legacy_fields["aiml_roles"],
            cyber_roles=legacy_fields["cyber_roles"],
            aiml_skills=legacy_fields["aiml_skills"],
            cyber_skills=legacy_fields["cyber_skills"],
            aiml_roadmap=legacy_fields["aiml_roadmap"],
            cyber_roadmap=legacy_fields["cyber_roadmap"],
            industry_insights=legacy_fields["industry_insights"],
        )
        analysis = self.create_analysis(profile_id, payload)
        setattr(analysis, "career_analysis_source", engine.career_analysis_source)
        setattr(analysis, "branch_analysis_source", branch_analysis_source)
        logger.info(
            "analysis_generation_source profile_id=%s user_id=%s career_source=%s branch_source=%s",
            profile_id,
            user_id,
            engine.career_analysis_source,
            branch_analysis_source,
        )
        return analysis
