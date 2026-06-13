from __future__ import annotations

from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.career_analysis import CareerAnalysis
from app.models.student_profile import StudentProfile
from app.schemas.admission_intelligence import (
    AdmissionCounselorBriefRead,
    AdmissionDashboardRead,
    AdmissionLeadRead,
    AdmissionMetricsRead,
)


_PRIORITY_ORDER = {"urgent": 0, "high": 1, "medium": 2, "low": 3}
_MAX_ITEMS = 5


class AdmissionIntelligenceService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_dashboard(self, limit: int = 12) -> AdmissionDashboardRead:
        profiles = self._twelfth_profiles()
        analyses = self._latest_analyses([profile.id for profile in profiles])
        leads = [
            self._lead_from_profile(profile, analyses.get(profile.id))
            for profile in profiles
        ]
        metrics = self._build_metrics(leads)

        safe_limit = max(1, min(int(limit or 12), 100))
        leads.sort(
            key=lambda lead: (
                _PRIORITY_ORDER.get(lead.priority, 99),
                -lead.created_at.timestamp(),
                -lead.profile_id,
            )
        )

        return AdmissionDashboardRead(metrics=metrics, leads=leads[:safe_limit])

    def _twelfth_profiles(self) -> list[StudentProfile]:
        return list(
            self.db.scalars(
                select(StudentProfile)
                .where(StudentProfile.user_type == "twelfth_student")
                .order_by(StudentProfile.created_at.desc(), StudentProfile.id.desc())
            ).all()
        )

    def _latest_analyses(self, profile_ids: list[int]) -> dict[int, CareerAnalysis]:
        if not profile_ids:
            return {}

        rank = func.row_number().over(
            partition_by=CareerAnalysis.student_profile_id,
            order_by=(CareerAnalysis.created_at.desc(), CareerAnalysis.id.desc()),
        ).label("rank")
        ranked = (
            select(
                CareerAnalysis.id.label("analysis_id"),
                CareerAnalysis.student_profile_id.label("profile_id"),
                rank,
            )
            .subquery()
        )
        latest = (
            select(ranked.c.analysis_id, ranked.c.profile_id)
            .where(ranked.c.rank == 1)
            .subquery()
        )
        analyses = self.db.scalars(
            select(CareerAnalysis)
            .join(latest, latest.c.analysis_id == CareerAnalysis.id)
            .where(latest.c.profile_id.in_(profile_ids))
        ).all()
        return {analysis.student_profile_id: analysis for analysis in analyses}

    def _build_metrics(self, leads: list[AdmissionLeadRead]) -> AdmissionMetricsRead:
        return AdmissionMetricsRead(
            total_twelfth_profiles=len(leads),
            analyzed_profiles=sum(1 for lead in leads if lead.status != "needs_analysis"),
            needs_analysis=sum(1 for lead in leads if lead.status == "needs_analysis"),
            high_intent=sum(1 for lead in leads if self._is_high_intent_lead(lead)),
            wrong_branch_risk=sum(
                1
                for lead in leads
                if lead.status == "wrong_branch_risk"
                or lead.status == "needs_analysis"
            ),
            ready_for_counseling=sum(
                1 for lead in leads if lead.status == "ready_for_counseling"
            ),
        )

    def _lead_from_profile(
        self,
        profile: StudentProfile,
        analysis: CareerAnalysis | None,
    ) -> AdmissionLeadRead:
        summary = _safe_dict(getattr(analysis, "program_fit_summary", None))
        recommendations = _safe_list(getattr(analysis, "program_recommendations", None))
        expectation_checks = _safe_list(
            getattr(analysis, "expectation_reality_checks", None)
        )
        first_year_roadmap = _safe_list(getattr(analysis, "first_year_roadmap", None))
        counselor_summary = _safe_dict(getattr(analysis, "counselor_summary", None))
        evidence = _safe_list(getattr(analysis, "rag_evidence", None))

        recommended_program = self._recommended_program(summary, recommendations)
        confidence = _safe_int(summary.get("confidence"))
        evidence_titles = self._evidence_titles(evidence)
        lost_reason_signals = self._lost_reason_signals(
            profile,
            analysis,
            confidence,
            len(evidence_titles),
        )
        status, priority = self._status_and_priority(
            analysis,
            confidence,
            lost_reason_signals,
        )
        brief = self._build_brief_from_parts(
            summary=summary,
            recommendations=recommendations,
            expectation_checks=expectation_checks,
            first_year_roadmap=first_year_roadmap,
            counselor_summary=counselor_summary,
            evidence_titles=evidence_titles,
            confidence=confidence,
            recommended_program=recommended_program,
        )

        lead = AdmissionLeadRead(
            profile_id=profile.id,
            student_name=profile.name,
            current_interest=self._current_interest(profile),
            preferred_stream=self._preferred_stream(profile),
            recommended_program=recommended_program,
            confidence=confidence,
            status=status,
            priority=priority,
            lost_reason_signals=lost_reason_signals,
            counselor_brief=brief,
            created_at=profile.created_at,
        )
        setattr(lead, "_high_intent", self._is_high_intent(profile, analysis))
        return lead

    def _build_brief(self, analysis: CareerAnalysis | None) -> AdmissionCounselorBriefRead:
        summary = _safe_dict(getattr(analysis, "program_fit_summary", None))
        recommendations = _safe_list(getattr(analysis, "program_recommendations", None))
        return self._build_brief_from_parts(
            summary=summary,
            recommendations=recommendations,
            expectation_checks=_safe_list(
                getattr(analysis, "expectation_reality_checks", None)
            ),
            first_year_roadmap=_safe_list(getattr(analysis, "first_year_roadmap", None)),
            counselor_summary=_safe_dict(getattr(analysis, "counselor_summary", None)),
            evidence_titles=self._evidence_titles(
                _safe_list(getattr(analysis, "rag_evidence", None))
            ),
            confidence=_safe_int(summary.get("confidence")),
            recommended_program=self._recommended_program(summary, recommendations),
        )

    def _lost_reason_signals(
        self,
        profile: StudentProfile,
        analysis: CareerAnalysis | None,
        confidence: int | None,
        evidence_count: int,
    ) -> list[str]:
        del profile
        summary = _safe_dict(getattr(analysis, "program_fit_summary", None))
        recommendations = _safe_list(getattr(analysis, "program_recommendations", None))
        recommended_program = self._recommended_program(summary, recommendations)
        expectation_checks = _safe_list(
            getattr(analysis, "expectation_reality_checks", None)
        )
        signals: list[str] = []
        if analysis is None or not summary:
            signals.append("missing_analysis")
        if confidence is not None and confidence < 65:
            signals.append("low_confidence")
        if expectation_checks:
            signals.append("expectation_mismatch")
        if evidence_count <= 0:
            signals.append("weak_evidence")
        if not recommended_program or confidence is None:
            signals.append("unclear_fit")
        return signals

    def _status_and_priority(
        self,
        analysis: CareerAnalysis | None,
        confidence: int | None,
        signals: list[str],
    ) -> tuple[str, str]:
        summary = _safe_dict(getattr(analysis, "program_fit_summary", None))
        recommendations = _safe_list(getattr(analysis, "program_recommendations", None))
        recommended_program = self._recommended_program(summary, recommendations)
        evidence_count = len(
            self._evidence_titles(_safe_list(getattr(analysis, "rag_evidence", None)))
        )

        if analysis is None or not summary:
            status = "needs_analysis"
        elif (
            (confidence is not None and confidence < 65)
            or len(signals) >= 2
            or not recommended_program
        ):
            status = "wrong_branch_risk"
        elif confidence is not None and confidence >= 75 and recommended_program and evidence_count > 0:
            status = "ready_for_counseling"
        else:
            status = "in_review"

        if status in {"needs_analysis", "wrong_branch_risk"}:
            priority = "urgent"
        elif status == "ready_for_counseling":
            priority = "low"
        elif confidence is not None and confidence >= 70:
            priority = "medium"
        elif signals:
            priority = "high"
        else:
            priority = "low"
        return status, priority

    def _build_brief_from_parts(
        self,
        *,
        summary: dict[str, Any],
        recommendations: list[Any],
        expectation_checks: list[Any],
        first_year_roadmap: list[Any],
        counselor_summary: dict[str, Any],
        evidence_titles: list[str],
        confidence: int | None,
        recommended_program: str | None,
    ) -> AdmissionCounselorBriefRead:
        talking_points = _strings(counselor_summary.get("talking_points"))
        if not talking_points:
            talking_points = self._recommendation_reasons(recommendations)
        if not talking_points and recommended_program:
            talking_points = [f"Discuss fit for {recommended_program}."]
        if not talking_points:
            talking_points = ["Confirm interests, strengths, and admission readiness."]

        follow_up_questions = _strings(counselor_summary.get("follow_up_questions"))
        if not follow_up_questions:
            follow_up_questions = [
                "Which subject feels strongest right now?",
                "What career outcome do you expect from this program?",
            ]

        return AdmissionCounselorBriefRead(
            best_fit=_text(counselor_summary.get("best_fit")) or recommended_program,
            confidence=confidence,
            talking_points=talking_points[:_MAX_ITEMS],
            expectation_checks=self._expectation_check_texts(expectation_checks),
            first_year_actions=self._first_year_actions(first_year_roadmap),
            evidence_titles=evidence_titles[:_MAX_ITEMS],
            follow_up_questions=follow_up_questions[:_MAX_ITEMS],
        )

    def _recommended_program(
        self,
        summary: dict[str, Any],
        recommendations: list[Any],
    ) -> str | None:
        direct = _text(summary.get("recommended_program_name")) or _text(
            summary.get("recommended_program_id")
        )
        if direct:
            return direct
        for item in recommendations:
            if not isinstance(item, dict):
                continue
            program = _text(item.get("program_name")) or _text(item.get("program_id"))
            if program:
                return program
        return None

    def _recommendation_reasons(self, recommendations: list[Any]) -> list[str]:
        reasons: list[str] = []
        for item in recommendations:
            if not isinstance(item, dict):
                continue
            reasons.extend(_strings(item.get("reasons")))
            reasons.extend(_strings(item.get("fit_reasons")))
        return _unique(reasons)

    def _expectation_check_texts(self, expectation_checks: list[Any]) -> list[str]:
        texts: list[str] = []
        for item in expectation_checks:
            if isinstance(item, dict):
                expectation = _text(item.get("expectation")) or _text(
                    item.get("student_expectation")
                )
                reality = _text(item.get("reality")) or _text(item.get("reality_check"))
                note = _text(item.get("counselor_note"))
                if expectation and reality:
                    texts.append(f"{expectation} -> {reality}")
                elif note:
                    texts.append(note)
            else:
                text = _text(item)
                if text:
                    texts.append(text)
        return _unique(texts)[:_MAX_ITEMS]

    def _first_year_actions(self, roadmap: list[Any]) -> list[str]:
        actions: list[str] = []
        for item in roadmap:
            if isinstance(item, dict):
                actions.extend(_strings(item.get("actions")))
                action = _text(item.get("action"))
                if action:
                    actions.append(action)
                actions.extend(_strings(item.get("focus")))
                actions.extend(_strings(item.get("evidence_to_build")))
            else:
                text = _text(item)
                if text:
                    actions.append(text)
        return _unique(actions)[:_MAX_ITEMS]

    def _evidence_titles(self, evidence: list[Any]) -> list[str]:
        titles: list[str] = []
        for item in evidence:
            if isinstance(item, dict):
                title = (
                    _text(item.get("source_title"))
                    or _text(item.get("title"))
                    or _text(item.get("document_title"))
                )
                if title:
                    titles.append(title)
            else:
                text = _text(item)
                if text:
                    titles.append(text)
        return _unique(titles)[:_MAX_ITEMS]

    def _current_interest(self, profile: StudentProfile) -> str:
        for value in (
            _strings(getattr(profile, "interests", None))
            + _strings(getattr(profile, "subjects", None))
            + _strings(getattr(profile, "current_skills", None))
        ):
            return value
        return _text(getattr(profile, "target_industry", None)) or "Not captured"

    def _preferred_stream(self, profile: StudentProfile) -> str:
        return _text(getattr(profile, "specialization", None)) or _text(
            getattr(profile, "degree", None)
        ) or "Not captured"

    def _is_high_intent_lead(self, lead: AdmissionLeadRead) -> bool:
        return bool(getattr(lead, "_high_intent", False))

    def _is_high_intent(
        self,
        profile: StudentProfile,
        analysis: CareerAnalysis | None,
    ) -> bool:
        signals = (
            _strings(getattr(profile, "interests", None))
            + _strings(getattr(profile, "subjects", None))
            + _strings(getattr(profile, "current_skills", None))
        )
        strength = {
            _text(getattr(profile, "programming_interest", None)),
            _text(getattr(profile, "math_strength", None)),
        }
        return len(signals) >= 2 and (
            analysis is not None or bool(strength.intersection({"medium", "high"}))
        )


def _safe_dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _safe_list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def _safe_int(value: Any) -> int | None:
    try:
        if value is None or value == "":
            return None
        return int(round(float(value)))
    except (TypeError, ValueError):
        return None


def _strings(value: Any) -> list[str]:
    if isinstance(value, list):
        return [item for item in (_text(item) for item in value) if item]
    text = _text(value)
    return [text] if text else []


def _text(value: Any) -> str | None:
    if not isinstance(value, str):
        return None
    text = " ".join(value.split())
    return text or None


def _unique(values: list[str]) -> list[str]:
    seen: set[str] = set()
    unique_values: list[str] = []
    for value in values:
        key = value.casefold()
        if key in seen:
            continue
        seen.add(key)
        unique_values.append(value)
    return unique_values
