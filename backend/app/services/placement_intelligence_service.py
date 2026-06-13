from __future__ import annotations

from collections import Counter, defaultdict
from typing import Any

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.models.career_analysis import CareerAnalysis
from app.models.company_fit import CompanyFit
from app.models.employability_score import EmployabilityScore
from app.models.internship_readiness import InternshipReadiness
from app.models.placement_risk import PlacementRisk
from app.models.role_gap_analysis import RoleGapAnalysis
from app.models.student_profile import StudentProfile
from app.schemas.placement_intelligence import (
    CompanyReadinessRead,
    FacultyAdvisorNoteRead,
    PlacementDashboardRead,
    PlacementMetricsRead,
    PlacementStudentSignalRead,
    SkillEvidenceLedgerRead,
    TrainingROISignalRead,
)


_PRIORITY_ORDER = {"urgent": 0, "high": 1, "medium": 2, "low": 3}


class PlacementIntelligenceService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_dashboard(self, limit: int = 12) -> PlacementDashboardRead:
        profiles = self._college_profiles()
        profile_ids = [profile.id for profile in profiles]
        employability_scores = self._latest_records(EmployabilityScore, profile_ids)
        placement_risks = self._latest_records(PlacementRisk, profile_ids)
        company_fits = self._latest_records(CompanyFit, profile_ids)
        role_gaps = self._latest_records(RoleGapAnalysis, profile_ids)
        career_analyses = self._latest_records(CareerAnalysis, profile_ids)
        internships = self._latest_records(InternshipReadiness, profile_ids)

        signals = [
            self._student_signal(
                profile,
                employability_scores.get(profile.id),
                placement_risks.get(profile.id),
                company_fits.get(profile.id),
                role_gaps.get(profile.id),
                career_analyses.get(profile.id),
                internships.get(profile.id),
            )
            for profile in profiles
        ]
        metrics = self._metrics(signals)
        signals.sort(
            key=lambda signal: (
                _PRIORITY_ORDER.get(signal.priority, 99),
                signal.employability_score if signal.employability_score is not None else -1,
                -signal.created_at.timestamp(),
                -signal.profile_id,
            )
        )
        safe_limit = max(1, min(int(limit or 12), 100))

        return PlacementDashboardRead(
            metrics=metrics,
            students=signals[:safe_limit],
            company_radar=self._company_radar(
                signals, company_fits, role_gaps, career_analyses
            ),
            training_roi=self._training_roi(role_gaps, career_analyses),
            faculty_notes=self._faculty_notes(signals),
        )

    def _college_profiles(self) -> list[StudentProfile]:
        return list(
            self.db.scalars(
                select(StudentProfile)
                .where(
                    or_(
                        StudentProfile.user_type.is_(None),
                        StudentProfile.user_type != "twelfth_student",
                    )
                )
                .order_by(StudentProfile.created_at.desc(), StudentProfile.id.desc())
            ).all()
        )

    def _latest_records(self, model, profile_ids: list[int]) -> dict[int, object]:
        if not profile_ids:
            return {}

        rank = func.row_number().over(
            partition_by=model.student_profile_id,
            order_by=(model.created_at.desc(), model.id.desc()),
        ).label("rank")
        ranked = (
            select(
                model.id.label("record_id"),
                model.student_profile_id.label("profile_id"),
                rank,
            )
            .where(model.student_profile_id.in_(profile_ids))
            .subquery()
        )
        latest = (
            select(ranked.c.record_id, ranked.c.profile_id)
            .where(ranked.c.rank == 1)
            .subquery()
        )
        records = self.db.scalars(
            select(model)
            .join(latest, latest.c.record_id == model.id)
            .where(latest.c.profile_id.in_(profile_ids))
        ).all()
        return {record.student_profile_id: record for record in records}

    def _student_signal(
        self,
        profile: StudentProfile,
        employability: EmployabilityScore | None,
        risk: PlacementRisk | None,
        company_fit: CompanyFit | None,
        role_gap: RoleGapAnalysis | None,
        career_analysis: CareerAnalysis | None,
        internship: InternshipReadiness | None,
    ) -> PlacementStudentSignalRead:
        evidence = self._evidence_ledger(
            profile, employability, role_gap, career_analysis, internship
        )
        employability_score = _safe_int(getattr(employability, "overall_score", None))
        risk_level = getattr(risk, "risk_level", None)
        top_company, top_company_score = _top_company(company_fit)
        high_risk = (
            risk_level == "High"
            or (employability_score is not None and employability_score < 50)
            or evidence.evidence_score < 45
        )
        placement_ready = (
            employability_score is not None
            and employability_score >= 70
            and risk_level == "Low"
            and evidence.evidence_score >= 70
        )

        if high_risk:
            status = "high_risk"
            priority = "urgent"
        elif placement_ready:
            status = "placement_ready"
            priority = "low"
        else:
            status = "needs_training"
            priority = "high" if evidence.evidence_score < 60 else "medium"

        return PlacementStudentSignalRead(
            profile_id=profile.id,
            student_name=profile.name,
            program=_program(profile, career_analysis),
            employability_score=employability_score,
            placement_risk=risk_level,
            top_company=top_company,
            top_company_score=top_company_score,
            status=status,
            priority=priority,
            recommended_actions=_recommended_actions(
                status, evidence, employability_score, risk
            ),
            evidence=evidence,
            created_at=profile.created_at,
        )

    def _evidence_ledger(
        self,
        profile: StudentProfile,
        employability: EmployabilityScore | None,
        role_gap: RoleGapAnalysis | None,
        career_analysis: CareerAnalysis | None,
        internship: InternshipReadiness | None,
    ) -> SkillEvidenceLedgerRead:
        project_count = _safe_int(getattr(profile, "projects", None), 0) or 0
        internship_count = _safe_int(getattr(profile, "internships", None), 0) or 0
        certification_count = _safe_int(getattr(profile, "certifications", None), 0) or 0
        resume_quality = _safe_int(getattr(employability, "resume_quality", None), 0) or 0
        internship_readiness = (
            _safe_int(getattr(internship, "readiness_score", None), 0) or 0
        )

        evidence_score = _clamp(
            min(25, project_count * 10)
            + min(20, internship_count * 12)
            + min(15, certification_count * 7)
            + int(round(_clamp(resume_quality) * 0.25))
            + int(round(_clamp(internship_readiness) * 0.15))
        )
        gaps = _unique(
            _skills_from_role_gaps(getattr(role_gap, "role_gaps", None))
            + _skills_from_skill_gaps(getattr(career_analysis, "skill_gaps", None))
        )
        strengths: list[str] = []
        if project_count:
            strengths.append("Project portfolio")
        if internship_count:
            strengths.append("Internship exposure")
        if certification_count:
            strengths.append("Certifications")
        if resume_quality >= 70:
            strengths.append("Resume quality")
        if internship_readiness >= 70:
            strengths.append("Internship readiness")

        return SkillEvidenceLedgerRead(
            evidence_score=evidence_score,
            project_count=project_count,
            internship_count=internship_count,
            certification_count=certification_count,
            resume_quality=_clamp(resume_quality),
            internship_readiness=_clamp(internship_readiness),
            strengths=strengths,
            gaps=gaps,
        )

    def _company_radar(
        self,
        signals: list[PlacementStudentSignalRead],
        company_fits: dict[int, CompanyFit],
        role_gaps: dict[int, RoleGapAnalysis],
        career_analyses: dict[int, CareerAnalysis],
    ) -> list[CompanyReadinessRead]:
        del signals, role_gaps, career_analyses
        company_scores: dict[str, list[int]] = defaultdict(list)
        company_missing: dict[str, list[str]] = defaultdict(list)
        buckets: dict[str, Counter[str]] = defaultdict(Counter)

        for company_fit in company_fits.values():
            for match in _safe_list(getattr(company_fit, "matches", None)):
                if not isinstance(match, dict):
                    continue
                company = _company_name(match)
                score = _company_score(match, 0)
                if not company:
                    continue
                company_scores[company].append(score or 0)
                company_missing[company].extend(_skills_from_value(match))
                if (score or 0) >= 75:
                    buckets[company]["ready"] += 1
                elif (score or 0) >= 60:
                    buckets[company]["watch"] += 1
                else:
                    buckets[company]["blocked"] += 1

        radar = [
            CompanyReadinessRead(
                company=company,
                average_score=int(sum(scores) / len(scores)),
                ready_count=buckets[company]["ready"],
                watch_count=buckets[company]["watch"],
                blocked_count=buckets[company]["blocked"],
                missing_skills=_unique(company_missing[company]),
            )
            for company, scores in company_scores.items()
            if scores
        ]
        radar.sort(
            key=lambda item: (
                -(item.ready_count + item.watch_count),
                -item.average_score,
                item.company,
            )
        )
        return radar

    def _training_roi(
        self,
        role_gaps: dict[int, RoleGapAnalysis],
        career_analyses: dict[int, CareerAnalysis],
    ) -> list[TrainingROISignalRead]:
        affected_profiles: dict[str, set[int]] = defaultdict(set)
        skill_order: dict[str, int] = {}

        def add_skill(skill: str, profile_id: int) -> None:
            if not skill:
                return
            skill_order.setdefault(skill, len(skill_order))
            affected_profiles[skill].add(profile_id)

        for profile_id, role_gap in role_gaps.items():
            for skill in _skills_from_role_gaps(getattr(role_gap, "role_gaps", None)):
                add_skill(skill, profile_id)
        for profile_id, career_analysis in career_analyses.items():
            for skill in _skills_from_skill_gaps(
                getattr(career_analysis, "skill_gaps", None)
            ):
                add_skill(skill, profile_id)

        roi = []
        for skill, profile_set in affected_profiles.items():
            affected = len(profile_set)
            lift = min(25, 8 + affected * 3)
            roi.append(
                TrainingROISignalRead(
                    skill=skill,
                    affected_students=affected,
                    expected_readiness_lift=lift,
                    priority="high" if affected >= 2 else "medium",
                )
            )
        roi.sort(
            key=lambda item: (
                -item.affected_students,
                -item.expected_readiness_lift,
                skill_order.get(item.skill, 999),
            )
        )
        return roi

    def _faculty_notes(
        self, signals: list[PlacementStudentSignalRead]
    ) -> list[FacultyAdvisorNoteRead]:
        notes = []
        for signal in signals:
            if signal.priority not in {"urgent", "high"}:
                continue
            focus_areas = signal.evidence.gaps[:4] or signal.recommended_actions[:3]
            if not focus_areas:
                focus_areas = ["Placement readiness"]
            notes.append(
                FacultyAdvisorNoteRead(
                    profile_id=signal.profile_id,
                    student_name=signal.student_name,
                    escalation_level=signal.priority,
                    focus_areas=focus_areas,
                    note=(
                        f"{signal.student_name} needs {signal.priority} placement "
                        f"intervention focused on {', '.join(focus_areas[:3])}."
                    ),
                )
            )
        notes.sort(
            key=lambda note: (
                _PRIORITY_ORDER.get(note.escalation_level, 99),
                note.student_name,
            )
        )
        return notes

    def _metrics(
        self, signals: list[PlacementStudentSignalRead]
    ) -> PlacementMetricsRead:
        employability_values = [
            signal.employability_score
            for signal in signals
            if signal.employability_score is not None
        ]
        return PlacementMetricsRead(
            total_college_profiles=len(signals),
            placement_ready=sum(
                1 for signal in signals if signal.status == "placement_ready"
            ),
            needs_training=sum(
                1 for signal in signals if signal.status == "needs_training"
            ),
            high_risk=sum(1 for signal in signals if signal.status == "high_risk"),
            company_ready=sum(
                1
                for signal in signals
                if signal.top_company_score is not None and signal.top_company_score >= 75
            ),
            evidence_complete=sum(
                1 for signal in signals if signal.evidence.evidence_score >= 75
            ),
            average_employability=(
                round(sum(employability_values) / len(employability_values))
                if employability_values
                else None
            ),
        )


def _top_company(company_fit: CompanyFit | None) -> tuple[str | None, int | None]:
    matches = [
        match
        for match in _safe_list(getattr(company_fit, "matches", None))
        if isinstance(match, dict)
    ]
    if not matches:
        return None, None
    top = max(
        matches,
        key=lambda match: _company_score(match, 0) or 0,
    )
    company = _company_name(top)
    score = _company_score(top)
    return company, score


def _program(
    profile: StudentProfile, career_analysis: CareerAnalysis | None
) -> str:
    for key in ("recommended_branch",):
        value = _clean_text(getattr(career_analysis, key, None))
        if value:
            return value
    return " - ".join(
        value
        for value in [
            _clean_text(getattr(profile, "degree", None)),
            _clean_text(getattr(profile, "specialization", None)),
        ]
        if value
    )


def _recommended_actions(
    status: str,
    evidence: SkillEvidenceLedgerRead,
    employability_score: int | None,
    risk: PlacementRisk | None,
) -> list[str]:
    actions: list[str] = []
    if status == "placement_ready":
        actions.append("Schedule company-specific interview practice.")
    if status == "high_risk":
        actions.append("Assign faculty mentor and weekly placement recovery plan.")
    if employability_score is None or employability_score < 70:
        actions.append("Improve employability score through targeted skill labs.")
    if evidence.resume_quality < 70:
        actions.append("Complete resume review with verified project outcomes.")
    if evidence.internship_readiness < 70:
        actions.append("Finish internship readiness action plan.")
    for reason in _safe_list(getattr(risk, "reasons", None)):
        text = _clean_text(reason)
        if text:
            actions.append(text)
    for gap in evidence.gaps[:3]:
        actions.append(f"Close {gap} gap.")
    return _unique(actions)


def _skills_from_role_gaps(value: Any) -> list[str]:
    skills: list[str] = []
    for item in _safe_list(value):
        if isinstance(item, dict):
            skills.extend(_skills_from_value(item))
        else:
            text = _clean_text(item)
            if text:
                skills.append(text)
    return skills


def _skills_from_skill_gaps(value: Any) -> list[str]:
    skills: list[str] = []
    for item in _safe_list(value):
        if isinstance(item, dict):
            for key in ("skill", "name", "skill_name", "missing_skill"):
                text = _clean_text(item.get(key))
                if text:
                    skills.append(text)
                    break
            else:
                skills.extend(_skills_from_value(item))
        else:
            text = _clean_text(item)
            if text:
                skills.append(text)
    return skills


def _skills_from_value(value: Any) -> list[str]:
    skills: list[str] = []
    if not isinstance(value, dict):
        return skills
    for key in (
        "missing_skills",
        "skill_gaps",
        "required_skills",
        "gaps",
        "skills",
    ):
        raw = value.get(key)
        if isinstance(raw, list):
            skills.extend(_clean_text(item) for item in raw if _clean_text(item))
        elif isinstance(raw, str):
            skills.append(raw)
    return [_clean_text(skill) for skill in skills if _clean_text(skill)]


def _company_name(match: dict[str, Any]) -> str:
    for key in ("company", "company_name", "name", "employer"):
        text = _clean_text(match.get(key))
        if text:
            return text
    return ""


def _company_score(match: dict[str, Any], default: int | None = None) -> int | None:
    for key in ("score", "fit_score", "match_score"):
        if key in match:
            return _safe_int(match.get(key), default)
    return default


def _safe_list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def _safe_int(value: Any, default: int | None = None) -> int | None:
    try:
        if value is None:
            return default
        return int(value)
    except (TypeError, ValueError):
        return default


def _clamp(value: int | None, low: int = 0, high: int = 100) -> int:
    return max(low, min(high, int(value or 0)))


def _clean_text(value: Any) -> str:
    return str(value).strip() if value is not None else ""


def _unique(values: list[str]) -> list[str]:
    seen = set()
    unique_values = []
    for value in values:
        text = _clean_text(value)
        key = text.casefold()
        if text and key not in seen:
            seen.add(key)
            unique_values.append(text)
    return unique_values
