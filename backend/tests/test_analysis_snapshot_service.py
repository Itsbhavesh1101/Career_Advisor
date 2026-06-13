from __future__ import annotations

from types import SimpleNamespace

import pytest

from app.services import analysis_snapshot_service as snapshot_module
from app.services.analysis_snapshot_service import AnalysisSnapshotService


class _FakeDB:
    def __init__(self, profile: object | None) -> None:
        self._profile = profile

    def get(self, model, profile_id: int):
        del model
        profile = self._profile
        if profile is None:
            return None
        return profile if getattr(profile, "id", None) == profile_id else None


def _patch_snapshot_dependencies(
    monkeypatch: pytest.MonkeyPatch,
    *,
    recommendations: list[dict] | None = None,
    career_source: str = "unknown",
    branch_source: str = "not_applicable",
) -> None:
    resolved_recommendations = recommendations if recommendations is not None else [{"role": "AI Engineer", "score": 80}]

    class _FakeCareerAnalysisService:
        def __init__(self, db):
            del db

        def generate_analysis(self, profile_id: int, user_id: int, *, allow_admin: bool = False):
            del profile_id, user_id, allow_admin
            return SimpleNamespace(
                id=101,
                career_recommendations=resolved_recommendations,
                career_analysis_source=career_source,
                branch_analysis_source=branch_source,
                program_fit_summary=(
                    {"recommended_program_id": "sirt-btech-cse-aiml"}
                    if branch_source != "not_applicable"
                    else None
                ),
                rag_evidence=(
                    [{"source_title": "AIML Foundation"}]
                    if branch_source != "not_applicable"
                    else None
                ),
            )

    class _FakePlacementRiskService:
        def __init__(self, db):
            del db

        def generate(self, profile):
            del profile
            return SimpleNamespace(id=201)

    class _FakeInternshipReadinessService:
        def __init__(self, db):
            del db

        def generate(self, profile):
            del profile
            return SimpleNamespace(id=202)

    class _FakeEmployabilityService:
        def __init__(self, db):
            del db

        def compute_score(self, profile_id: int, user_id: int, *, allow_admin: bool = False):
            del profile_id, user_id, allow_admin
            return SimpleNamespace(id=203)

    class _FakeCompanyFitService:
        def __init__(self, db):
            del db

        def generate(self, profile):
            del profile
            return SimpleNamespace(id=204)

    class _FakeRoleGapService:
        def __init__(self, db):
            del db

        def generate(self, profile):
            del profile
            return SimpleNamespace(id=205)

    monkeypatch.setattr(snapshot_module, "CareerAnalysisService", _FakeCareerAnalysisService)
    monkeypatch.setattr(snapshot_module, "PlacementRiskService", _FakePlacementRiskService)
    monkeypatch.setattr(snapshot_module, "InternshipReadinessService", _FakeInternshipReadinessService)
    monkeypatch.setattr(snapshot_module, "EmployabilityService", _FakeEmployabilityService)
    monkeypatch.setattr(snapshot_module, "CompanyFitService", _FakeCompanyFitService)
    monkeypatch.setattr(snapshot_module, "RoleGapService", _FakeRoleGapService)


def test_generate_snapshot_for_college_profile_includes_all_module_ids(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _patch_snapshot_dependencies(monkeypatch)
    profile = SimpleNamespace(id=1, user_id=10, user_type="college_student")
    service = AnalysisSnapshotService(_FakeDB(profile))

    snapshot = service.generate_snapshot(profile_id=1, user_id=10)

    assert snapshot["profile_id"] == 1
    assert snapshot["career_analysis_id"] == 101
    assert snapshot["placement_risk_id"] == 201
    assert snapshot["internship_readiness_id"] == 202
    assert snapshot["employability_score_id"] == 203
    assert snapshot["company_fit_id"] == 204
    assert snapshot["role_gap_id"] == 205


def test_generate_snapshot_for_twelfth_profile_skips_college_only_modules(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _patch_snapshot_dependencies(monkeypatch)
    profile = SimpleNamespace(id=2, user_id=20, user_type="twelfth_student")
    service = AnalysisSnapshotService(_FakeDB(profile))

    snapshot = service.generate_snapshot(profile_id=2, user_id=20)

    assert snapshot["profile_id"] == 2
    assert snapshot["career_analysis_id"] == 101
    assert snapshot["placement_risk_id"] == 201
    assert snapshot["internship_readiness_id"] == 202
    assert "employability_score_id" not in snapshot
    assert "company_fit_id" not in snapshot
    assert "role_gap_id" not in snapshot


def test_generate_snapshot_requires_profile_access(monkeypatch: pytest.MonkeyPatch) -> None:
    _patch_snapshot_dependencies(monkeypatch)
    profile = SimpleNamespace(id=3, user_id=30, user_type="college_student")
    service = AnalysisSnapshotService(_FakeDB(profile))

    with pytest.raises(ValueError, match="Profile not found"):
        service.generate_snapshot(profile_id=3, user_id=99)


def test_generate_snapshot_marks_empty_career_recommendations_blocked(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _patch_snapshot_dependencies(monkeypatch, recommendations=[])
    profile = SimpleNamespace(id=4, user_id=40, user_type="college_student")
    service = AnalysisSnapshotService(_FakeDB(profile))

    snapshot = service.generate_snapshot(profile_id=4, user_id=40)

    assert snapshot["verifier"]["status"] == "blocked"
    assert any(
        "career recommendations" in item.lower()
        for item in snapshot["verifier"]["blockers"]
    )
    assert snapshot["agent_stages"][-1]["stage"] == "verifier_agent"
    assert snapshot["agent_stages"][-1]["status"] == "failed"


def test_generate_snapshot_includes_analysis_sources(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _patch_snapshot_dependencies(
        monkeypatch,
        career_source="llm",
        branch_source="rule_engine",
    )
    profile = SimpleNamespace(id=5, user_id=50, user_type="twelfth_student")
    service = AnalysisSnapshotService(_FakeDB(profile))

    snapshot = service.generate_snapshot(profile_id=5, user_id=50)

    assert snapshot["career_analysis_source"] == "llm"
    assert snapshot["branch_analysis_source"] == "rule_engine"


def test_generate_snapshot_records_agent_stages_and_verifier(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _patch_snapshot_dependencies(
        monkeypatch,
        career_source="llm",
        branch_source="not_applicable",
    )
    profile = SimpleNamespace(id=6, user_id=60, user_type="college_student")
    service = AnalysisSnapshotService(_FakeDB(profile))

    snapshot = service.generate_snapshot(profile_id=6, user_id=60)

    assert snapshot["snapshot_version"] == "agentic-snapshot-v1"
    assert snapshot["verifier"]["status"] == "approved"
    assert snapshot["verifier"]["confidence"] >= 85
    assert [stage["stage"] for stage in snapshot["agent_stages"]] == [
        "profile_understanding",
        "career_pathway_agent",
        "placement_risk_agent",
        "internship_readiness_agent",
        "employability_agent",
        "company_readiness_agent",
        "role_gap_agent",
        "verifier_agent",
    ]


def test_generate_snapshot_records_twelfth_program_fit_stage(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _patch_snapshot_dependencies(
        monkeypatch,
        career_source="llm",
        branch_source="llm",
    )
    profile = SimpleNamespace(id=7, user_id=70, user_type="twelfth_student")
    service = AnalysisSnapshotService(_FakeDB(profile))

    snapshot = service.generate_snapshot(profile_id=7, user_id=70)

    stages = {stage["stage"]: stage for stage in snapshot["agent_stages"]}
    assert stages["program_fit_agent"]["status"] == "completed"
    assert stages["employability_agent"]["status"] == "skipped"
    assert snapshot["verifier"]["status"] in {"approved", "approved_with_warnings"}
