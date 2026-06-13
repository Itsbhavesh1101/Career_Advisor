from __future__ import annotations

from types import SimpleNamespace

import pytest

from app.schemas.career_analysis import CareerAnalysisCreate
from app.services import career_analysis_service as service_module
from app.services.career_analysis_service import CareerAnalysisService


class _FakeDB:
    def __init__(self, profile: object | None = None) -> None:
        self.profile = profile
        self.added = None
        self.committed = False
        self.refreshed = None

    def get(self, _model, profile_id: int):
        return (
            self.profile
            if self.profile is not None and profile_id == self.profile.id
            else None
        )

    def add(self, row) -> None:
        self.added = row

    def commit(self) -> None:
        self.committed = True

    def refresh(self, row) -> None:
        self.refreshed = row


def _program(
    program_id: str,
    program_name: str,
    *,
    is_active: bool = True,
) -> SimpleNamespace:
    return SimpleNamespace(
        program_id=program_id,
        program_name=program_name,
        is_active=is_active,
        priority_skills=["Python"],
        career_paths=["Software Developer"],
        admission_fit_signals=["Problem solving"],
        reality_checks=["Requires consistent practice."],
    )


def _catalog(*programs: SimpleNamespace) -> SimpleNamespace:
    return SimpleNamespace(
        version="test-catalog-v1",
        schools=[
            SimpleNamespace(
                school_name="SIRT Engineering",
                is_active=True,
                programs=list(programs),
            )
        ],
    )


def _patch_catalog(
    monkeypatch: pytest.MonkeyPatch,
    catalog: SimpleNamespace,
) -> None:
    class _FakeInstitutionConfigService:
        def __init__(self, db):
            del db

        def get_catalog(self):
            return catalog

    monkeypatch.setattr(
        service_module,
        "InstitutionConfigService",
        _FakeInstitutionConfigService,
    )


class _FakeRAGEvidence:
    def __init__(self, payload: dict) -> None:
        self.payload = payload

    def model_dump(self) -> dict:
        return dict(self.payload)


def _patch_rag_service(
    monkeypatch: pytest.MonkeyPatch,
    *,
    results: list[dict] | None = None,
    error: Exception | None = None,
    calls: list[dict] | None = None,
    init_calls: list[object] | None = None,
) -> None:
    class _FakeRAGService:
        def __init__(self, db=None) -> None:
            if init_calls is not None:
                init_calls.append(db)

        def search(self, query, *, program_ids=None, limit=5):
            if calls is not None:
                calls.append(
                    {
                        "query": query,
                        "program_ids": program_ids,
                        "limit": limit,
                    }
                )
            if error is not None:
                raise error
            return [_FakeRAGEvidence(item) for item in results or []]

    monkeypatch.setattr(service_module, "RAGService", _FakeRAGService)


def test_create_analysis_persists_program_fit_fields() -> None:
    db = _FakeDB()
    service = CareerAnalysisService(db)

    analysis = service.create_analysis(
        1,
        CareerAnalysisCreate(
            career_recommendations=[{"role": "AI Engineer", "score": 80}],
            skill_gaps=[{"skill": "Python", "priority": "high"}],
            learning_roadmap=[{"stage": "Foundation", "topics": ["Python"]}],
            salary_insights={"currency": "INR", "estimate_min": 300000},
            industry_trends=[{"trend": "AI", "impact": "high"}],
            institution_config_version="sage-initial-2026-05",
            program_fit_summary={
                "recommended_program_id": "sirt-btech-cse-aiml",
                "recommended_program_name": "B.Tech CSE - AIML",
                "confidence": 86,
                "summary": "Strong fit.",
            },
            program_recommendations=[
                {
                    "program_id": "sirt-btech-cse-aiml",
                    "program_name": "B.Tech CSE - AIML",
                    "fit_score": 86,
                }
            ],
            expectation_reality_checks=[
                {
                    "expectation": "AI starts with model training.",
                    "reality": "It starts with programming and mathematics.",
                    "counselor_note": "Align expectations.",
                }
            ],
            first_year_roadmap=[
                {
                    "term": "Semester 1",
                    "focus": ["Python"],
                    "evidence_to_build": ["Mini project"],
                }
            ],
            counselor_summary={"best_fit": "B.Tech CSE - AIML"},
        ),
    )

    assert analysis.institution_config_version == "sage-initial-2026-05"
    assert analysis.program_fit_summary["recommended_program_id"] == "sirt-btech-cse-aiml"
    assert analysis.program_recommendations[0]["fit_score"] == 86
    assert analysis.expectation_reality_checks[0]["counselor_note"] == "Align expectations."
    assert analysis.first_year_roadmap[0]["term"] == "Semester 1"
    assert analysis.counselor_summary == {"best_fit": "B.Tech CSE - AIML"}
    assert db.added is analysis
    assert db.committed is True
    assert db.refreshed is analysis


def test_generate_analysis_for_twelfth_student_stores_program_fit_and_legacy_fields(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    profile = SimpleNamespace(id=2, user_id=20, user_type="twelfth_student")
    db = _FakeDB(profile)
    calls: dict[str, object] = {}
    _patch_catalog(
        monkeypatch,
        _catalog(
            _program("sirt-btech-cse-aiml", "B.Tech CSE - AIML"),
            _program("sirt-btech-cse-cyber", "B.Tech CSE - Cyber Security"),
        ),
    )

    class _FakeEngine:
        career_analysis_source = "llm"
        branch_analysis_source = "not_applicable"
        program_fit_analysis_source = "llm"

        def generate_career_recommendations(self, profile_arg):
            return [{"role": "AI Engineer", "score": 88}]

        def generate_skill_gaps(self, profile_arg):
            return [{"skill": "Python", "priority": "high"}]

        def generate_learning_roadmap(self, profile_arg):
            return [{"stage": "Foundation", "topics": ["Python"]}]

        def generate_salary_insights(self, profile_arg):
            return {"currency": "INR", "estimate_min": 400000}

        def generate_industry_trends(self, profile_arg):
            return [{"trend": "AI", "impact": "high"}]

        def generate_branch_analysis(self, profile_arg):
            raise AssertionError("legacy branch generation should not be called")

        def generate_program_fit_analysis(
            self,
            profile_arg,
            program_options,
            catalog_version,
            rag_context=None,
        ):
            calls["profile"] = profile_arg
            calls["program_options"] = program_options
            calls["catalog_version"] = catalog_version
            return {
                "program_fit_summary": {
                    "recommended_program_id": "sirt-btech-cse-aiml",
                    "recommended_program_name": "B.Tech CSE - AIML",
                    "confidence": 91,
                    "summary": "Strong AI fit.",
                },
                "program_recommendations": [
                    {
                        "program_id": "sirt-btech-cse-aiml",
                        "program_name": "B.Tech CSE - AIML",
                        "school": "SIRT Engineering",
                        "fit_score": 91,
                        "fit_level": "High",
                        "reasons": ["Strong programming interest"],
                        "career_paths": ["Machine Learning Engineer"],
                        "priority_skills": ["Python", "Mathematics"],
                        "first_year_focus": ["Python foundations"],
                    },
                    {
                        "program_id": "sirt-btech-cse-cyber",
                        "program_name": "B.Tech CSE - Cyber Security",
                        "school": "SIRT Engineering",
                        "fit_score": 76,
                        "fit_level": "Medium",
                        "reasons": ["Good logical reasoning"],
                        "career_paths": ["Security Analyst"],
                        "priority_skills": ["Networking", "Linux"],
                        "first_year_focus": ["Networking basics"],
                    },
                ],
                "expectation_reality_checks": [
                    {
                        "expectation": "AI starts with model building.",
                        "reality": "AI starts with programming and math.",
                        "counselor_note": "Align learning curve.",
                    }
                ],
                "first_year_roadmap": [
                    {
                        "term": "Semester 1",
                        "focus": ["Python"],
                        "evidence_to_build": ["Mini project"],
                    }
                ],
                "counselor_summary": {
                    "best_fit": "B.Tech CSE - AIML",
                    "risk_flags": ["Math depth"],
                },
            }

    monkeypatch.setattr(service_module, "CareerAIEngine", _FakeEngine)

    analysis = CareerAnalysisService(db).generate_analysis(profile_id=2, user_id=20)

    assert calls["profile"] is profile
    assert calls["catalog_version"] == "test-catalog-v1"
    options = calls["program_options"]
    assert isinstance(options, list)
    assert any(option["program_id"] == "sirt-btech-cse-aiml" for option in options)
    assert all("school" in option for option in options)
    assert analysis.institution_config_version == "test-catalog-v1"
    assert (
        analysis.program_fit_summary["recommended_program_id"]
        == "sirt-btech-cse-aiml"
    )
    assert analysis.program_recommendations[0]["fit_score"] == 91
    assert "expecting" in analysis.expectation_reality_checks[0]["expectation"].lower()
    assert "python" in analysis.expectation_reality_checks[0]["reality"].lower()
    assert "Counselor" in analysis.expectation_reality_checks[0]["counselor_note"]
    assert analysis.first_year_roadmap[0]["term"] == "Semester 1"
    assert analysis.counselor_summary["best_fit"] == "B.Tech CSE - AIML"
    assert analysis.aiml_score == 91
    assert analysis.cyber_security_score == 76
    assert analysis.recommended_branch == "AIML"
    assert analysis.branch_reasoning == [{"reason": "Strong programming interest"}]
    assert analysis.aiml_roles == [{"role": "Machine Learning Engineer", "score": 91}]
    assert analysis.cyber_roles == [{"role": "Security Analyst", "score": 76}]
    assert analysis.aiml_skills == ["Python", "Mathematics"]
    assert analysis.cyber_skills == ["Networking", "Linux"]
    assert analysis.aiml_roadmap == [{"year": 1, "topics": ["Python foundations"]}]
    assert analysis.cyber_roadmap == [{"year": 1, "topics": ["Networking basics"]}]
    assert analysis.industry_insights[0]["branch"] == "AIML"
    assert analysis.career_analysis_source == "llm"
    assert analysis.branch_analysis_source == "llm"


def test_twelfth_expectation_checks_are_personalized_counselor_advice(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    profile = SimpleNamespace(
        id=12,
        user_id=120,
        user_type="twelfth_student",
        name="Aditi Sharma",
        degree="B.Tech",
        specialization="CSE AIML",
        subjects=["Mathematics", "Computer Science"],
        interests=["AI tools", "data projects"],
        current_skills=["Python"],
        math_strength="medium",
        logical_reasoning="high",
        programming_interest="high",
    )
    db = _FakeDB(profile)
    _patch_catalog(
        monkeypatch,
        _catalog(
            _program("sirt-btech-cse-aiml", "B.Tech CSE - AIML"),
            _program("sirt-btech-cse-cyber", "B.Tech CSE - Cyber Security"),
        ),
    )

    class _FakeEngine:
        career_analysis_source = "llm"
        branch_analysis_source = "not_applicable"
        program_fit_analysis_source = "llm"

        def generate_career_recommendations(self, profile_arg):
            return [{"role": "AI Engineer", "score": 88}]

        def generate_skill_gaps(self, profile_arg):
            return [{"skill": "Python", "priority": "high"}]

        def generate_learning_roadmap(self, profile_arg):
            return [{"stage": "Foundation", "topics": ["Python"]}]

        def generate_salary_insights(self, profile_arg):
            return {"currency": "INR", "estimate_min": 400000}

        def generate_industry_trends(self, profile_arg):
            return [{"trend": "AI", "impact": "high"}]

        def generate_program_fit_analysis(
            self,
            profile_arg,
            program_options,
            catalog_version,
            rag_context=None,
        ):
            del profile_arg, program_options, catalog_version, rag_context
            return {
                "program_fit_summary": {
                    "recommended_program_id": "sirt-btech-cse-aiml",
                    "recommended_program_name": "B.Tech CSE - AIML",
                    "confidence": 88,
                    "summary": "Strong fit.",
                },
                "program_recommendations": [
                    {
                        "program_id": "sirt-btech-cse-aiml",
                        "program_name": "B.Tech CSE - AIML",
                        "school": "SIRT Engineering",
                        "fit_score": 88,
                        "fit_level": "High",
                        "reasons": ["Strong AI interest"],
                        "career_paths": ["Machine Learning Engineer"],
                        "priority_skills": ["Python", "Mathematics", "Data Handling"],
                        "first_year_focus": ["Python foundations"],
                    }
                ],
                "expectation_reality_checks": [
                    {
                        "expectation": "AI starts with model building.",
                        "reality": "First year focuses on programming and mathematics.",
                        "counselor_note": "Explain the foundation path.",
                    }
                ],
                "first_year_roadmap": [],
                "counselor_summary": {},
            }

    monkeypatch.setattr(service_module, "CareerAIEngine", _FakeEngine)

    analysis = CareerAnalysisService(db).generate_analysis(profile_id=12, user_id=120)

    checks = analysis.expectation_reality_checks
    assert checks
    assert checks[0]["expectation"] != "AI starts with model building."
    combined = " ".join(
        f"{item['expectation']} {item['reality']} {item['counselor_note']}"
        for item in checks
    ).lower()
    assert "aditi" not in combined
    assert "ai tools" in combined
    assert "python" in combined
    assert "mathematics" in combined
    assert "weekly" in combined or "counselor" in combined


def test_twelfth_program_fit_keeps_every_active_program_even_when_llm_returns_one(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    profile = SimpleNamespace(
        id=20,
        user_id=200,
        user_type="twelfth_student",
        subjects=["Mathematics", "Computer Science"],
        interests=["software", "business"],
        current_skills=["Python"],
        degree="B.Tech",
        specialization="CSE",
    )
    db = _FakeDB(profile)
    _patch_catalog(
        monkeypatch,
        _catalog(
            _program("sirt-btech-cse-aiml", "B.Tech CSE - AIML"),
            _program("sirt-btech-cse-cyber", "B.Tech CSE - Cyber Security"),
            _program("sirt-btech-cse-core", "B.Tech CSE"),
            _program("sage-bba", "BBA"),
        ),
    )

    class _FakeEngine:
        career_analysis_source = "llm"
        branch_analysis_source = "not_applicable"
        program_fit_analysis_source = "llm"

        def generate_career_recommendations(self, profile_arg):
            return [{"role": "Software Developer", "score": 82}]

        def generate_skill_gaps(self, profile_arg):
            return [{"skill": "Data Structures", "priority": "high"}]

        def generate_learning_roadmap(self, profile_arg):
            return [{"stage": "Foundation", "topics": ["Programming"]}]

        def generate_salary_insights(self, profile_arg):
            return {"currency": "INR", "estimate_min": 350000, "estimate_max": 700000}

        def generate_industry_trends(self, profile_arg):
            return [{"trend": "Software hiring", "impact": "high"}]

        def generate_program_fit_analysis(
            self,
            profile_arg,
            program_options,
            catalog_version,
            rag_context=None,
        ):
            del profile_arg, program_options, catalog_version, rag_context
            return {
                "program_fit_summary": {
                    "recommended_program_id": "sirt-btech-cse-aiml",
                    "recommended_program_name": "B.Tech CSE - AIML",
                    "confidence": 86,
                    "summary": "Strong AI fit.",
                },
                "program_recommendations": [
                    {
                        "program_id": "sirt-btech-cse-aiml",
                        "program_name": "B.Tech CSE - AIML",
                        "school": "SIRT Engineering",
                        "fit_score": 86,
                        "fit_level": "High",
                        "reasons": ["Strong programming interest"],
                        "career_paths": ["Machine Learning Engineer"],
                        "priority_skills": ["Python"],
                        "first_year_focus": ["Python foundations"],
                    }
                ],
                "expectation_reality_checks": [
                    {
                        "expectation": "AI starts with model building.",
                        "reality": "AI starts with programming and math.",
                        "counselor_note": "Set expectations.",
                    }
                ],
                "first_year_roadmap": [
                    {
                        "term": "Semester 1",
                        "focus": ["Programming"],
                        "evidence_to_build": ["Mini project"],
                    }
                ],
                "counselor_summary": {
                    "best_fit": "B.Tech CSE - AIML",
                    "risk_flags": [],
                    "talking_points": ["Discuss daily practice."],
                    "follow_up_questions": ["Can you practice daily?"],
                },
            }

    monkeypatch.setattr(service_module, "CareerAIEngine", _FakeEngine)

    analysis = CareerAnalysisService(db).generate_analysis(profile_id=20, user_id=200)

    recommendation_ids = {
        item["program_id"] for item in analysis.program_recommendations
    }
    assert recommendation_ids == {
        "sirt-btech-cse-aiml",
        "sirt-btech-cse-cyber",
        "sirt-btech-cse-core",
        "sage-bba",
    }
    assert analysis.program_recommendations[0]["program_id"] == "sirt-btech-cse-aiml"
    fallback = next(
        item
        for item in analysis.program_recommendations
        if item["program_id"] == "sage-bba"
    )
    assert fallback["fit_level"] in {"Medium", "Low"}
    assert fallback["reasons"]
    assert fallback["first_year_focus"]


def test_twelfth_analysis_persists_rag_evidence(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    profile = SimpleNamespace(
        id=6,
        user_id=60,
        user_type="twelfth_student",
        degree="B.Tech",
        specialization="AIML",
        subjects=["Mathematics", "Computer Science"],
        interests=["AI", "Python"],
        current_skills=["Python"],
    )
    db = _FakeDB(profile)
    calls: dict[str, object] = {}
    rag_calls: list[dict] = []
    rag_init_calls: list[object] = []
    rag_payload = {
        "chunk_id": "program-aiml-test",
        "source_title": "AIML Foundation Test Evidence",
        "source_type": "program",
        "excerpt": "AIML requires Python and mathematics.",
        "score": 4.5,
        "tags": ["AIML"],
        "program_ids": ["sirt-btech-cse-aiml"],
    }
    _patch_catalog(
        monkeypatch,
        _catalog(_program("sirt-btech-cse-aiml", "B.Tech CSE - AIML")),
    )
    _patch_rag_service(
        monkeypatch,
        results=[rag_payload],
        calls=rag_calls,
        init_calls=rag_init_calls,
    )

    class _FakeEngine:
        career_analysis_source = "llm"
        branch_analysis_source = "not_applicable"
        program_fit_analysis_source = "llm"

        def generate_career_recommendations(self, profile_arg):
            return [{"role": "AI Engineer", "score": 88}]

        def generate_skill_gaps(self, profile_arg):
            return [{"skill": "Python", "priority": "high"}]

        def generate_learning_roadmap(self, profile_arg):
            return [{"stage": "Foundation", "topics": ["Python"]}]

        def generate_salary_insights(self, profile_arg):
            return {"currency": "INR", "estimate_min": 400000}

        def generate_industry_trends(self, profile_arg):
            return [{"trend": "AI", "impact": "high"}]

        def generate_branch_analysis(self, profile_arg):
            raise AssertionError("legacy branch generation should not be called")

        def generate_program_fit_analysis(
            self,
            profile_arg,
            program_options,
            catalog_version,
            rag_context=None,
        ):
            calls["rag_context"] = rag_context
            return {
                "program_fit_summary": {
                    "recommended_program_id": "sirt-btech-cse-aiml",
                    "recommended_program_name": "B.Tech CSE - AIML",
                    "confidence": 91,
                    "summary": "Strong AI fit.",
                },
                "program_recommendations": [
                    {
                        "program_id": "sirt-btech-cse-aiml",
                        "program_name": "B.Tech CSE - AIML",
                        "fit_score": 91,
                        "reasons": ["Strong programming interest"],
                        "career_paths": ["Machine Learning Engineer"],
                        "priority_skills": ["Python"],
                        "first_year_focus": ["Python foundations"],
                    }
                ],
                "expectation_reality_checks": [],
                "first_year_roadmap": [],
                "counselor_summary": {},
            }

    monkeypatch.setattr(service_module, "CareerAIEngine", _FakeEngine)

    analysis = CareerAnalysisService(db).generate_analysis(profile_id=6, user_id=60)

    assert analysis.rag_evidence
    assert rag_init_calls == [db]
    assert analysis.rag_evidence == [rag_payload]
    assert calls["rag_context"] == analysis.rag_evidence
    assert rag_calls == [
        {
            "query": (
                "B.Tech AIML Mathematics Computer Science AI Python Python "
                "B.Tech CSE - AIML"
            ),
            "program_ids": ["sirt-btech-cse-aiml"],
            "limit": 5,
        }
    ]


def test_twelfth_analysis_empty_rag_results_persist_empty_evidence(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    profile = SimpleNamespace(
        id=7,
        user_id=70,
        user_type="twelfth_student",
        degree="B.Tech",
        specialization="AIML",
        subjects=["Mathematics"],
        interests=["AI"],
        current_skills=["Python"],
    )
    db = _FakeDB(profile)
    calls: dict[str, object] = {}
    _patch_catalog(
        monkeypatch,
        _catalog(_program("sirt-btech-cse-aiml", "B.Tech CSE - AIML")),
    )
    _patch_rag_service(monkeypatch, results=[])

    class _FakeEngine:
        career_analysis_source = "llm"
        branch_analysis_source = "not_applicable"
        program_fit_analysis_source = "llm"

        def generate_career_recommendations(self, profile_arg):
            return []

        def generate_skill_gaps(self, profile_arg):
            return []

        def generate_learning_roadmap(self, profile_arg):
            return []

        def generate_salary_insights(self, profile_arg):
            return {}

        def generate_industry_trends(self, profile_arg):
            return []

        def generate_branch_analysis(self, profile_arg):
            raise AssertionError("legacy branch generation should not be called")

        def generate_program_fit_analysis(
            self,
            profile_arg,
            program_options,
            catalog_version,
            rag_context=None,
        ):
            calls["rag_context"] = rag_context
            return {
                "program_fit_summary": {
                    "recommended_program_id": "sirt-btech-cse-aiml",
                    "recommended_program_name": "B.Tech CSE - AIML",
                    "confidence": 80,
                    "summary": "Fit can be assessed without retrieved evidence.",
                },
                "program_recommendations": [
                    {
                        "program_id": "sirt-btech-cse-aiml",
                        "program_name": "B.Tech CSE - AIML",
                        "fit_score": 80,
                        "reasons": ["Programming interest"],
                        "career_paths": [],
                        "priority_skills": [],
                        "first_year_focus": [],
                    }
                ],
                "expectation_reality_checks": [],
                "first_year_roadmap": [],
                "counselor_summary": {},
            }

    monkeypatch.setattr(service_module, "CareerAIEngine", _FakeEngine)

    analysis = CareerAnalysisService(db).generate_analysis(profile_id=7, user_id=70)

    assert calls["rag_context"] == []
    assert analysis.rag_evidence == []


def test_twelfth_analysis_rag_exception_persists_empty_evidence(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    profile = SimpleNamespace(
        id=8,
        user_id=80,
        user_type="twelfth_student",
        degree="B.Tech",
        specialization="AIML",
        subjects=["Mathematics"],
        interests=["AI"],
        current_skills=["Python"],
    )
    db = _FakeDB(profile)
    calls: dict[str, object] = {}
    _patch_catalog(
        monkeypatch,
        _catalog(_program("sirt-btech-cse-aiml", "B.Tech CSE - AIML")),
    )
    _patch_rag_service(monkeypatch, error=RuntimeError("RAG unavailable"))

    class _FakeEngine:
        career_analysis_source = "llm"
        branch_analysis_source = "not_applicable"
        program_fit_analysis_source = "llm"

        def generate_career_recommendations(self, profile_arg):
            return []

        def generate_skill_gaps(self, profile_arg):
            return []

        def generate_learning_roadmap(self, profile_arg):
            return []

        def generate_salary_insights(self, profile_arg):
            return {}

        def generate_industry_trends(self, profile_arg):
            return []

        def generate_branch_analysis(self, profile_arg):
            raise AssertionError("legacy branch generation should not be called")

        def generate_program_fit_analysis(
            self,
            profile_arg,
            program_options,
            catalog_version,
            rag_context=None,
        ):
            calls["rag_context"] = rag_context
            return {
                "program_fit_summary": {
                    "recommended_program_id": "sirt-btech-cse-aiml",
                    "recommended_program_name": "B.Tech CSE - AIML",
                    "confidence": 80,
                    "summary": "Fit can be assessed after RAG failure.",
                },
                "program_recommendations": [
                    {
                        "program_id": "sirt-btech-cse-aiml",
                        "program_name": "B.Tech CSE - AIML",
                        "fit_score": 80,
                        "reasons": ["Programming interest"],
                        "career_paths": [],
                        "priority_skills": [],
                        "first_year_focus": [],
                    }
                ],
                "expectation_reality_checks": [],
                "first_year_roadmap": [],
                "counselor_summary": {},
            }

    monkeypatch.setattr(service_module, "CareerAIEngine", _FakeEngine)

    analysis = CareerAnalysisService(db).generate_analysis(profile_id=8, user_id=80)

    assert calls["rag_context"] == []
    assert analysis.rag_evidence == []


def test_generate_analysis_uses_summary_match_for_cyber_legacy_reasoning(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    profile = SimpleNamespace(id=4, user_id=40, user_type="twelfth_student")
    db = _FakeDB(profile)
    _patch_catalog(
        monkeypatch,
        _catalog(
            _program("sirt-btech-cse-aiml", "B.Tech CSE - AIML"),
            _program("sirt-btech-cse-cyber", "B.Tech CSE - Cyber Security"),
        ),
    )

    class _FakeEngine:
        career_analysis_source = "llm"
        branch_analysis_source = "not_applicable"
        program_fit_analysis_source = "llm"

        def generate_career_recommendations(self, profile_arg):
            return [{"role": "Security Analyst", "score": 87}]

        def generate_skill_gaps(self, profile_arg):
            return []

        def generate_learning_roadmap(self, profile_arg):
            return []

        def generate_salary_insights(self, profile_arg):
            return {}

        def generate_industry_trends(self, profile_arg):
            return []

        def generate_branch_analysis(self, profile_arg):
            raise AssertionError("legacy branch generation should not be called")

        def generate_program_fit_analysis(
            self,
            profile_arg,
            program_options,
            catalog_version,
            rag_context=None,
        ):
            del profile_arg, program_options, catalog_version, rag_context
            return {
                "program_fit_summary": {
                    "recommended_program_id": "sirt-btech-cse-cyber",
                    "recommended_program_name": "B.Tech CSE - Cyber Security",
                    "confidence": 88,
                    "summary": "Strong cyber fit.",
                },
                "program_recommendations": [
                    {
                        "program_id": "sirt-btech-cse-aiml",
                        "program_name": "B.Tech CSE - AIML",
                        "fit_score": 70,
                        "reasons": ["AI interest is secondary"],
                        "career_paths": ["AI Application Developer"],
                        "priority_skills": ["Python"],
                        "first_year_focus": ["Programming"],
                    },
                    {
                        "program_id": "sirt-btech-cse-cyber",
                        "program_name": "B.Tech CSE - Cyber Security",
                        "fit_score": 88,
                        "reasons": ["Strong systems investigation interest"],
                        "career_paths": ["Security Analyst"],
                        "priority_skills": ["Networking"],
                        "first_year_focus": ["Linux basics"],
                    },
                ],
                "expectation_reality_checks": [],
                "first_year_roadmap": [],
                "counselor_summary": {},
            }

    monkeypatch.setattr(service_module, "CareerAIEngine", _FakeEngine)

    analysis = CareerAnalysisService(db).generate_analysis(profile_id=4, user_id=40)

    assert analysis.recommended_branch == "Cyber Security"
    assert analysis.branch_reasoning == [
        {"reason": "Strong systems investigation interest"}
    ]
    assert analysis.industry_insights[1]["branch"] == "Cyber Security"


def test_generate_analysis_with_empty_active_catalog_skips_program_fit(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    profile = SimpleNamespace(id=5, user_id=50, user_type="twelfth_student")
    db = _FakeDB(profile)
    _patch_catalog(
        monkeypatch,
        _catalog(_program("inactive-program", "Inactive Program", is_active=False)),
    )

    class _FakeEngine:
        career_analysis_source = "llm"
        branch_analysis_source = "not_applicable"
        program_fit_analysis_source = "not_applicable"

        def generate_career_recommendations(self, profile_arg):
            return [{"role": "Software Developer", "score": 80}]

        def generate_skill_gaps(self, profile_arg):
            return [{"skill": "Python"}]

        def generate_learning_roadmap(self, profile_arg):
            return [{"stage": "Foundation"}]

        def generate_salary_insights(self, profile_arg):
            return {"currency": "INR"}

        def generate_industry_trends(self, profile_arg):
            return [{"trend": "Software"}]

        def generate_branch_analysis(self, profile_arg):
            raise AssertionError("legacy branch generation should not be called")

        def generate_program_fit_analysis(
            self,
            profile_arg,
            program_options,
            catalog_version,
            rag_context=None,
        ):
            raise AssertionError("program-fit generation should not be called")

    monkeypatch.setattr(service_module, "CareerAIEngine", _FakeEngine)

    analysis = CareerAnalysisService(db).generate_analysis(profile_id=5, user_id=50)

    assert analysis.institution_config_version is None
    assert analysis.program_fit_summary is None
    assert analysis.program_recommendations is None
    assert analysis.expectation_reality_checks is None
    assert analysis.first_year_roadmap is None
    assert analysis.counselor_summary is None
    assert analysis.recommended_branch is None
    assert analysis.branch_reasoning is None
    assert analysis.industry_insights is None
    assert analysis.branch_analysis_source == "catalog_unavailable"


def test_generate_analysis_for_college_student_skips_program_fit(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    profile = SimpleNamespace(id=3, user_id=30, user_type="college_student")
    db = _FakeDB(profile)

    class _FakeEngine:
        career_analysis_source = "llm"
        branch_analysis_source = "not_applicable"
        program_fit_analysis_source = "not_applicable"

        def generate_career_recommendations(self, profile_arg):
            return [{"role": "Backend Developer", "score": 82}]

        def generate_skill_gaps(self, profile_arg):
            return [{"skill": "Databases", "priority": "medium"}]

        def generate_learning_roadmap(self, profile_arg):
            return [{"stage": "Projects", "topics": ["APIs"]}]

        def generate_salary_insights(self, profile_arg):
            return {"currency": "INR", "estimate_min": 350000}

        def generate_industry_trends(self, profile_arg):
            return [{"trend": "Cloud", "impact": "medium"}]

        def generate_branch_analysis(self, profile_arg):
            raise AssertionError("branch generation should not be called")

        def generate_program_fit_analysis(
            self,
            profile_arg,
            program_options,
            catalog_version,
            rag_context=None,
        ):
            raise AssertionError("program-fit generation should not be called")

    monkeypatch.setattr(service_module, "CareerAIEngine", _FakeEngine)

    analysis = CareerAnalysisService(db).generate_analysis(profile_id=3, user_id=30)

    assert analysis.institution_config_version is None
    assert analysis.program_fit_summary is None
    assert analysis.program_recommendations is None
    assert analysis.expectation_reality_checks is None
    assert analysis.first_year_roadmap is None
    assert analysis.counselor_summary is None
    assert analysis.aiml_score is None
    assert analysis.cyber_security_score is None
    assert analysis.recommended_branch is None
    assert analysis.branch_reasoning is None
    assert analysis.aiml_roles is None
    assert analysis.cyber_roles is None
    assert analysis.aiml_skills is None
    assert analysis.cyber_skills is None
    assert analysis.aiml_roadmap is None
    assert analysis.cyber_roadmap is None
    assert analysis.industry_insights is None
    assert analysis.career_analysis_source == "llm"
    assert analysis.branch_analysis_source == "not_applicable"
