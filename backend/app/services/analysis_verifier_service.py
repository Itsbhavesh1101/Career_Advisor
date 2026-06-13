from __future__ import annotations

from typing import Any


class AnalysisVerifierService:
    def verify(
        self,
        summary: dict[str, Any],
        *,
        career_recommendations: list[dict[str, Any]],
    ) -> dict[str, Any]:
        blockers: list[str] = []
        warnings: list[str] = []
        user_type = str(summary.get("user_type") or "college_student")
        evidence_count = self._coerce_evidence_count(summary.get("evidence_count"), warnings)
        stages = summary.get("agent_stages") or []

        if not career_recommendations:
            blockers.append("Generated analysis is missing career recommendations.")
        if not summary.get("career_analysis_id"):
            blockers.append("Career analysis output reference is missing.")
        if user_type != "twelfth_student" and not summary.get("employability_score_id"):
            blockers.append("College student snapshot is missing employability scoring.")
        if user_type == "twelfth_student" and not summary.get("program_fit_summary"):
            warnings.append("Twelfth-student snapshot has no program-fit summary.")
        if user_type == "twelfth_student" and evidence_count == 0:
            warnings.append("Program-fit recommendation has no retrieved institution evidence.")
        if not stages:
            warnings.append("No agent stage metadata was recorded.")
        if any(stage.get("status") == "failed" for stage in stages if isinstance(stage, dict)):
            blockers.append("One or more agent stages failed.")

        confidence = 92
        confidence -= len(warnings) * 8
        confidence -= len(blockers) * 25
        confidence = max(0, min(100, confidence))

        if blockers:
            status = "blocked"
        elif warnings:
            status = "approved_with_warnings"
        else:
            status = "approved"

        return {
            "status": status,
            "confidence": confidence,
            "blockers": blockers,
            "warnings": warnings,
            "evidence_count": evidence_count,
            "next_best_actions": self._next_best_actions(user_type, warnings, blockers),
        }

    def _coerce_evidence_count(self, value: Any, warnings: list[str]) -> int:
        if value in (None, ""):
            return 0
        try:
            evidence_count = int(value)
        except (TypeError, ValueError):
            warnings.append("Evidence count was invalid and treated as zero.")
            return 0
        if evidence_count < 0:
            warnings.append("Evidence count was negative and treated as zero.")
            return 0
        return evidence_count

    def _next_best_actions(
        self,
        user_type: str,
        warnings: list[str],
        blockers: list[str],
    ) -> list[str]:
        if blockers:
            return [
                "Regenerate the analysis after checking profile completeness.",
                "Ask a counselor or placement owner to review missing outputs.",
            ]
        if user_type == "twelfth_student":
            actions = [
                "Review expectation reality checks with the student and parent.",
                "Confirm program fit using subject comfort, interest, and first-year effort.",
            ]
        else:
            actions = [
                "Review top skill gaps and assign a 30-day learning sprint.",
                "Use placement risk and company-fit outputs to prioritize interventions.",
            ]
        if warnings:
            actions.append("Review verifier warnings before using this snapshot for decisions.")
        return actions
