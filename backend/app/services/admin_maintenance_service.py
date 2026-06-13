from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlalchemy import String, cast, delete, func, or_, select, update
from sqlalchemy.orm import Session

from app.models.admin_management import AdminManagedItem
from app.models.analysis_job import AnalysisJob
from app.models.career_analysis import CareerAnalysis
from app.models.company_fit import CompanyFit
from app.models.employability_score import EmployabilityScore
from app.models.internship_readiness import InternshipReadiness
from app.models.notification import UserNotification
from app.models.placement_opportunity import PlacementCompany, PlacementOpportunity
from app.models.placement_risk import PlacementRisk
from app.models.psychometric_answer import PsychometricAnswer
from app.models.psychometric_question import PsychometricQuestion
from app.models.psychometric_result import PsychometricResult
from app.models.psychometric_session import PsychometricSession
from app.models.rag_document import RAGDocumentChunk, RAGDocumentSource
from app.models.resume_analysis import ResumeAnalysis
from app.models.role_gap_analysis import RoleGapAnalysis
from app.models.student_profile import StudentProfile
from app.models.user import User
from app.schemas.admin_maintenance import (
    AdminPresentationDemoDataPreviewRead,
    AdminPresentationDemoDataSeedResultRead,
    AdminSmokeDataCleanupPreviewRead,
    AdminSmokeDataCleanupResultRead,
)

SMOKE_CLEANUP_CONFIRMATION = "DELETE_SMOKE_TEST_DEMO_DATA"
PRESENTATION_DEMO_SEED_CONFIRMATION = "SEED_PRESENTATION_DEMO_DATA"
PRESENTATION_DEMO_MARKER = "presentation_demo_20260526"
PRESENTATION_DEMO_EMAILS = (
    "demo.presentation.twelfth@example.com",
    "demo.presentation.college@example.com",
)
PRESENTATION_DEMO_ITEM_SLUGS = (
    "presentation-demo-ai-foundation-bridge",
    "presentation-demo-aptitude-sprint",
    "presentation-demo-internship-lab",
    "presentation-demo-placement-company",
    "presentation-demo-counseling-policy",
    "presentation-demo-knowledge-template",
    "presentation-demo-homepage-notice",
)
PRESENTATION_DEMO_COMPANY_NAME = "TechNova Solutions"
PRESENTATION_DEMO_OPPORTUNITY_TITLE = "Associate Software Engineer - Campus Sprint"

_SAFE_EMAIL_PATTERNS = (
    "sage-smoke-%@example.com",
    "sage.smoke.%@example.com",
    "sage-live-%@example.com",
    "sage.live.%@example.com",
    "sage-e2e-%@example.com",
    "sage.e2e.%@example.com",
    "smoke.%@example.com",
    "test.%@example.com",
    "demo.%@example.com",
)

_SAFE_SOURCE_TITLE_PATTERNS = (
    "%smoke%",
    "%demo%",
    "test upload%",
    "% test upload%",
    "test source%",
    "% test source%",
)

_SAFE_SOURCE_TAG_PATTERNS = (
    '%"smoke"%',
    '%"test"%',
    '%"demo"%',
)


class AdminMaintenanceService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def preview_presentation_demo_data(self) -> AdminPresentationDemoDataPreviewRead:
        user_ids = self._presentation_demo_user_ids()
        profile_ids = self._profile_ids(user_ids)
        session_ids = self._quiz_session_ids(user_ids=user_ids, profile_ids=profile_ids)
        return AdminPresentationDemoDataPreviewRead(
            users=len(user_ids),
            profiles=len(profile_ids),
            career_analyses=self._count_by_profile(CareerAnalysis, profile_ids),
            resume_analyses=self._count_by_profile(ResumeAnalysis, profile_ids),
            employability_scores=self._count_by_profile(
                EmployabilityScore,
                profile_ids,
            ),
            placement_risks=self._count_by_profile(PlacementRisk, profile_ids),
            company_fits=self._count_by_profile(CompanyFit, profile_ids),
            role_gap_analyses=self._count_by_profile(RoleGapAnalysis, profile_ids),
            internship_readiness=self._count_by_profile(
                InternshipReadiness,
                profile_ids,
            ),
            quiz_sessions=len(session_ids),
            quiz_results=self._count_quiz_results(
                user_ids=user_ids,
                profile_ids=profile_ids,
                session_ids=session_ids,
            ),
            admin_managed_items=self._presentation_demo_admin_item_count(),
            placement_companies=self._presentation_demo_company_count(),
            placement_opportunities=self._presentation_demo_opportunity_count(),
            notifications=self._presentation_demo_notification_count(),
            sample_emails=self._presentation_demo_sample_emails(),
            sample_items=self._presentation_demo_sample_items(),
        )

    def seed_presentation_demo_data(
        self,
        *,
        confirm: str,
        created_by_user_id: int | None = None,
    ) -> AdminPresentationDemoDataSeedResultRead:
        if confirm != PRESENTATION_DEMO_SEED_CONFIRMATION:
            raise ValueError("Demo seed confirmation phrase does not match.")

        before = self.preview_presentation_demo_data()
        should_seed = (
            before.users < 2
            or before.profiles < 2
            or before.admin_managed_items < len(PRESENTATION_DEMO_ITEM_SLUGS)
            or before.placement_companies < 1
            or before.placement_opportunities < 1
            or before.notifications < 2
        )

        try:
            twelfth_user = self._ensure_demo_user(
                email=PRESENTATION_DEMO_EMAILS[0],
                supabase_user_id="demo-presentation-twelfth",
                student_type="twelfth_student",
            )
            college_user = self._ensure_demo_user(
                email=PRESENTATION_DEMO_EMAILS[1],
                supabase_user_id="demo-presentation-college",
                student_type="college_student",
            )
            self.db.flush()

            twelfth_profile = self._ensure_demo_profile(
                user=twelfth_user,
                name="Aditi Sharma",
                user_type="twelfth_student",
                degree="B.Tech",
                specialization="CSE AIML",
                twelfth_percentage=91.2,
                cgpa=0.0,
                subjects=["Mathematics", "Computer Science", "Physics"],
                interests=["AI tools", "data projects", "problem solving"],
                current_skills=["Python", "school-level statistics"],
                target_industry="Technology",
                projects=1,
                internships=0,
                certifications=1,
                math_strength="medium",
                logical_reasoning="high",
                programming_interest="high",
            )
            college_profile = self._ensure_demo_profile(
                user=college_user,
                name="Rohan Verma",
                user_type="college_student",
                degree="B.Tech",
                specialization="Computer Science",
                twelfth_percentage=84.5,
                cgpa=8.1,
                subjects=["Data Structures", "DBMS", "Operating Systems"],
                interests=["backend development", "cloud", "campus placements"],
                current_skills=["Python", "SQL", "React", "FastAPI"],
                target_industry="Software Engineering",
                projects=3,
                internships=1,
                certifications=2,
                math_strength="high",
                logical_reasoning="high",
                programming_interest="high",
            )
            self.db.flush()

            self._ensure_twelfth_demo_outputs(twelfth_profile)
            self._ensure_college_demo_outputs(college_profile)
            self._ensure_demo_admin_items(created_by_user_id=created_by_user_id)
            company = self._ensure_demo_company(created_by_user_id=created_by_user_id)
            self._ensure_demo_opportunity(
                company=company,
                created_by_user_id=created_by_user_id,
            )
            self._ensure_demo_notifications(
                twelfth_profile=twelfth_profile,
                college_profile=college_profile,
                created_by_user_id=created_by_user_id,
            )
            self.db.commit()
        except Exception:
            self.db.rollback()
            raise

        after = self.preview_presentation_demo_data()
        return AdminPresentationDemoDataSeedResultRead(
            **after.model_dump(),
            seeded=should_seed,
        )

    def preview_smoke_data_cleanup(self) -> AdminSmokeDataCleanupPreviewRead:
        user_ids = self._eligible_user_ids()
        profile_ids = self._profile_ids(user_ids)
        session_ids = self._quiz_session_ids(user_ids=user_ids, profile_ids=profile_ids)
        rag_source_ids = self._eligible_rag_source_ids()

        return AdminSmokeDataCleanupPreviewRead(
            users=len(user_ids),
            profiles=len(profile_ids),
            analysis_jobs=self._count_analysis_jobs(user_ids, profile_ids),
            career_analyses=self._count_by_profile(CareerAnalysis, profile_ids),
            resume_analyses=self._count_by_profile(ResumeAnalysis, profile_ids),
            employability_scores=self._count_by_profile(
                EmployabilityScore, profile_ids
            ),
            placement_risks=self._count_by_profile(PlacementRisk, profile_ids),
            company_fits=self._count_by_profile(CompanyFit, profile_ids),
            role_gap_analyses=self._count_by_profile(RoleGapAnalysis, profile_ids),
            internship_readiness=self._count_by_profile(
                InternshipReadiness, profile_ids
            ),
            quiz_sessions=len(session_ids),
            quiz_questions=self._count_by_session(PsychometricQuestion, session_ids),
            quiz_answers=self._count_by_session(PsychometricAnswer, session_ids),
            quiz_results=self._count_quiz_results(
                user_ids=user_ids,
                profile_ids=profile_ids,
                session_ids=session_ids,
            ),
            rag_sources=len(rag_source_ids),
            rag_chunks=self._count_rag_chunks(rag_source_ids),
            sample_emails=self._sample_emails(),
            sample_rag_titles=self._sample_rag_titles(),
        )

    def cleanup_smoke_data(
        self,
        *,
        confirm: str,
    ) -> AdminSmokeDataCleanupResultRead:
        if confirm != SMOKE_CLEANUP_CONFIRMATION:
            raise ValueError("Cleanup confirmation phrase does not match.")

        preview = self.preview_smoke_data_cleanup()
        user_ids = self._eligible_user_ids()
        profile_ids = self._profile_ids(user_ids)
        session_ids = self._quiz_session_ids(user_ids=user_ids, profile_ids=profile_ids)
        rag_source_ids = self._eligible_rag_source_ids()

        try:
            if session_ids:
                self.db.execute(
                    update(PsychometricSession)
                    .where(PsychometricSession.id.in_(session_ids))
                    .values(current_question_id=None)
                )
                self.db.execute(
                    delete(PsychometricAnswer).where(
                        PsychometricAnswer.session_id.in_(session_ids)
                    )
                )
                self.db.execute(
                    delete(PsychometricResult).where(
                        PsychometricResult.session_id.in_(session_ids)
                    )
                )
                self.db.execute(
                    delete(PsychometricQuestion).where(
                        PsychometricQuestion.session_id.in_(session_ids)
                    )
                )
                self.db.execute(
                    delete(PsychometricSession).where(
                        PsychometricSession.id.in_(session_ids)
                    )
                )

            if user_ids or profile_ids:
                analysis_predicates = []
                if user_ids:
                    analysis_predicates.append(AnalysisJob.user_id.in_(user_ids))
                if profile_ids:
                    analysis_predicates.append(
                        AnalysisJob.student_profile_id.in_(profile_ids)
                    )
                self.db.execute(delete(AnalysisJob).where(or_(*analysis_predicates)))

            self._delete_by_profile(ResumeAnalysis, profile_ids)
            self._delete_by_profile(EmployabilityScore, profile_ids)
            self._delete_by_profile(PlacementRisk, profile_ids)
            self._delete_by_profile(CompanyFit, profile_ids)
            self._delete_by_profile(RoleGapAnalysis, profile_ids)
            self._delete_by_profile(InternshipReadiness, profile_ids)
            self._delete_by_profile(CareerAnalysis, profile_ids)

            if profile_ids:
                self.db.execute(
                    delete(StudentProfile).where(StudentProfile.id.in_(profile_ids))
                )
            if user_ids:
                self.db.execute(delete(User).where(User.id.in_(user_ids)))

            if rag_source_ids:
                self.db.execute(
                    delete(RAGDocumentChunk).where(
                        RAGDocumentChunk.source_id.in_(rag_source_ids)
                    )
                )
                self.db.execute(
                    delete(RAGDocumentSource).where(
                        RAGDocumentSource.id.in_(rag_source_ids)
                    )
                )

            self.db.commit()
        except Exception:
            self.db.rollback()
            raise

        deleted = any(
            (
                preview.users,
                preview.profiles,
                preview.analysis_jobs,
                preview.career_analyses,
                preview.resume_analyses,
                preview.employability_scores,
                preview.placement_risks,
                preview.company_fits,
                preview.role_gap_analyses,
                preview.internship_readiness,
                preview.quiz_sessions,
                preview.quiz_questions,
                preview.quiz_answers,
                preview.quiz_results,
                preview.rag_sources,
                preview.rag_chunks,
            )
        )
        return AdminSmokeDataCleanupResultRead(
            **preview.model_dump(),
            deleted=deleted,
        )

    def _presentation_demo_user_ids(self) -> list[int]:
        return list(
            self.db.scalars(
                select(User.id)
                .where(func.lower(User.email).in_(PRESENTATION_DEMO_EMAILS))
                .order_by(User.id)
            )
        )

    def _presentation_demo_admin_item_count(self) -> int:
        return int(
            self.db.scalar(
                select(func.count(AdminManagedItem.id)).where(
                    AdminManagedItem.slug.in_(PRESENTATION_DEMO_ITEM_SLUGS)
                )
            )
            or 0
        )

    def _presentation_demo_company_count(self) -> int:
        return int(
            self.db.scalar(
                select(func.count(PlacementCompany.id)).where(
                    PlacementCompany.name == PRESENTATION_DEMO_COMPANY_NAME
                )
            )
            or 0
        )

    def _presentation_demo_opportunity_count(self) -> int:
        return int(
            self.db.scalar(
                select(func.count(PlacementOpportunity.id)).where(
                    PlacementOpportunity.title == PRESENTATION_DEMO_OPPORTUNITY_TITLE,
                    PlacementOpportunity.company == PRESENTATION_DEMO_COMPANY_NAME,
                )
            )
            or 0
        )

    def _presentation_demo_notification_count(self) -> int:
        return int(
            self.db.scalar(
                select(func.count(UserNotification.id)).where(
                    cast(UserNotification.event_metadata, String).like(
                        f"%{PRESENTATION_DEMO_MARKER}%"
                    )
                )
            )
            or 0
        )

    def _presentation_demo_sample_emails(self) -> list[str]:
        return list(
            self.db.scalars(
                select(User.email)
                .where(func.lower(User.email).in_(PRESENTATION_DEMO_EMAILS))
                .order_by(User.email)
            )
        )

    def _presentation_demo_sample_items(self) -> list[str]:
        admin_titles = list(
            self.db.scalars(
                select(AdminManagedItem.title)
                .where(AdminManagedItem.slug.in_(PRESENTATION_DEMO_ITEM_SLUGS))
                .order_by(AdminManagedItem.title)
                .limit(5)
            )
        )
        opportunity_titles = list(
            self.db.scalars(
                select(PlacementOpportunity.title)
                .where(PlacementOpportunity.title == PRESENTATION_DEMO_OPPORTUNITY_TITLE)
                .limit(2)
            )
        )
        return [*admin_titles, *opportunity_titles][:5]

    def _ensure_demo_user(
        self,
        *,
        email: str,
        supabase_user_id: str,
        student_type: str,
    ) -> User:
        row = self.db.scalar(
            select(User).where(func.lower(User.email) == email.lower())
        )
        if row is not None:
            return row
        row = User(
            supabase_user_id=supabase_user_id,
            email=email,
            password_hash="supabase-only",
            student_type=student_type,
        )
        self.db.add(row)
        return row

    def _ensure_demo_profile(
        self,
        *,
        user: User,
        name: str,
        user_type: str,
        degree: str,
        specialization: str,
        twelfth_percentage: float,
        cgpa: float,
        subjects: list[str],
        interests: list[str],
        current_skills: list[str],
        target_industry: str,
        projects: int,
        internships: int,
        certifications: int,
        math_strength: str,
        logical_reasoning: str,
        programming_interest: str,
    ) -> StudentProfile:
        row = self.db.scalar(
            select(StudentProfile).where(
                StudentProfile.user_id == user.id,
                StudentProfile.name == name,
            )
        )
        if row is not None:
            return row
        row = StudentProfile(
            user_id=user.id,
            name=name,
            twelfth_percentage=twelfth_percentage,
            cgpa=cgpa,
            degree=degree,
            specialization=specialization,
            current_skills=current_skills,
            interests=interests,
            target_industry=target_industry,
            projects=projects,
            internships=internships,
            certifications=certifications,
            subjects=subjects,
            math_strength=math_strength,
            logical_reasoning=logical_reasoning,
            programming_interest=programming_interest,
            user_type=user_type,
        )
        self.db.add(row)
        return row

    def _ensure_twelfth_demo_outputs(self, profile: StudentProfile) -> None:
        if not self._has_profile_record(CareerAnalysis, profile.id):
            self.db.add(
                CareerAnalysis(
                    student_profile_id=profile.id,
                    career_recommendations=[
                        {"role": "AI Product Engineer", "score": 86},
                        {"role": "Data Analyst", "score": 79},
                    ],
                    skill_gaps=[
                        {"skill": "Python projects", "priority": "high"},
                        {"skill": "Mathematics for AI", "priority": "medium"},
                    ],
                    learning_roadmap=[
                        {"stage": "Foundation", "topics": ["Python", "Statistics"]},
                        {"stage": "Proof", "topics": ["Mini data project"]},
                    ],
                    salary_insights={"currency": "INR", "estimate_min": 350000},
                    industry_trends=[
                        {"trend": "AI-assisted software roles", "impact": "high"}
                    ],
                    institution_config_version="presentation-demo",
                    program_fit_summary={
                        "recommended_program_id": "sirt-btech-cse-aiml",
                        "recommended_program_name": "B.Tech CSE - AIML",
                        "confidence": 88,
                        "summary": (
                            "Strong AIML direction if programming and mathematics "
                            "practice continue weekly."
                        ),
                    },
                    program_recommendations=[
                        {
                            "program_id": "sirt-btech-cse-aiml",
                            "program_name": "B.Tech CSE - AIML",
                            "school": "School of Engineering",
                            "fit_score": 88,
                            "fit_level": "High",
                            "reasons": [
                                "Interest in AI tools and Python is already visible."
                            ],
                            "career_paths": [
                                "Machine Learning Engineer",
                                "AI Product Engineer",
                            ],
                            "priority_skills": ["Python", "Mathematics", "Data Handling"],
                            "first_year_focus": ["Python foundations", "Statistics"],
                        }
                    ],
                    expectation_reality_checks=[
                        {
                            "expectation": (
                                "AI tools should immediately feel like advanced model work."
                            ),
                            "reality": (
                                "The first year still needs Python, mathematics, and "
                                "small projects before advanced model building."
                            ),
                            "counselor_note": (
                                "Discuss a weekly practice plan and review one mini "
                                "project before final branch confirmation."
                            ),
                        }
                    ],
                    first_year_roadmap=[
                        {
                            "term": "Semester 1",
                            "focus": ["Python", "mathematics bridge"],
                            "evidence_to_build": ["Data-cleaning mini project"],
                        }
                    ],
                    counselor_summary={
                        "best_fit": "B.Tech CSE - AIML",
                        "risk_flags": ["Needs consistent mathematics practice"],
                        "talking_points": ["Explain first-year workload clearly"],
                        "follow_up_questions": [
                            "Can the student practice Python weekly?"
                        ],
                    },
                )
            )
        self._ensure_demo_quiz_result(
            profile=profile,
            trait_scores={
                "analytical_reasoning": 0.82,
                "technical_curiosity": 0.88,
                "communication": 0.68,
            },
        )

    def _ensure_college_demo_outputs(self, profile: StudentProfile) -> None:
        if not self._has_profile_record(CareerAnalysis, profile.id):
            self.db.add(
                CareerAnalysis(
                    student_profile_id=profile.id,
                    career_recommendations=[
                        {"role": "Backend Developer", "score": 84},
                        {"role": "Cloud Support Engineer", "score": 78},
                    ],
                    skill_gaps=[
                        {"skill": "System design basics", "priority": "high"},
                        {"skill": "Interview DSA", "priority": "medium"},
                    ],
                    learning_roadmap=[
                        {"stage": "Portfolio", "topics": ["API project", "SQL depth"]},
                        {"stage": "Interview", "topics": ["DSA revision"]},
                    ],
                    salary_insights={
                        "currency": "INR",
                        "estimate_min": 450000,
                        "estimate_max": 800000,
                    },
                    industry_trends=[
                        {"trend": "Cloud-backed product teams", "impact": "high"}
                    ],
                )
            )
        if not self._has_profile_record(ResumeAnalysis, profile.id):
            self.db.add(
                ResumeAnalysis(
                    student_profile_id=profile.id,
                    file_name="presentation-demo-resume.pdf",
                    source_url="https://example.com/demo/resume.pdf",
                    extracted_skills=["Python", "SQL", "React", "FastAPI"],
                    projects=["Placement tracker API", "Internship readiness dashboard"],
                    experience=["Software internship - backend APIs"],
                    education=["B.Tech Computer Science"],
                    resume_score=82,
                    missing_keywords=["unit testing", "deployment"],
                    weak_sections=["metrics"],
                    suggestions=[
                        "Add quantified impact for the API project.",
                        "Mention deployment and test coverage clearly.",
                    ],
                )
            )
        self._ensure_profile_metric_outputs(profile)
        self._ensure_demo_quiz_result(
            profile=profile,
            trait_scores={
                "execution": 0.78,
                "technical_depth": 0.74,
                "interview_readiness": 0.69,
            },
        )

    def _ensure_profile_metric_outputs(self, profile: StudentProfile) -> None:
        if not self._has_profile_record(EmployabilityScore, profile.id):
            self.db.add(
                EmployabilityScore(
                    student_profile_id=profile.id,
                    overall_score=76,
                    academic_strength=78,
                    technical_skills=80,
                    industry_readiness=72,
                    resume_quality=82,
                )
            )
        if not self._has_profile_record(PlacementRisk, profile.id):
            self.db.add(
                PlacementRisk(
                    student_profile_id=profile.id,
                    risk_level="medium",
                    reasons=["Needs stronger interview DSA proof"],
                )
            )
        if not self._has_profile_record(CompanyFit, profile.id):
            self.db.add(
                CompanyFit(
                    student_profile_id=profile.id,
                    matches=[
                        {
                            "company": PRESENTATION_DEMO_COMPANY_NAME,
                            "fit_score": 82,
                            "reason": "Backend API and SQL evidence match role needs.",
                        }
                    ],
                )
            )
        if not self._has_profile_record(RoleGapAnalysis, profile.id):
            self.db.add(
                RoleGapAnalysis(
                    student_profile_id=profile.id,
                    role_gaps=[
                        {
                            "role": "Backend Developer",
                            "gaps": ["System design", "deployment proof"],
                        }
                    ],
                )
            )
        if not self._has_profile_record(InternshipReadiness, profile.id):
            self.db.add(
                InternshipReadiness(
                    student_profile_id=profile.id,
                    readiness_score=78,
                    readiness_level="ready_with_polish",
                    action_plan=[
                        "Update resume metrics",
                        "Prepare one API walkthrough",
                        "Apply to backend internships this week",
                    ],
                )
            )

    def _ensure_demo_quiz_result(
        self,
        *,
        profile: StudentProfile,
        trait_scores: dict,
    ) -> None:
        session_id = f"presentation-demo-{profile.id}"
        session = self.db.get(PsychometricSession, session_id)
        now = datetime.now(timezone.utc)
        if session is None:
            session = PsychometricSession(
                id=session_id,
                student_profile_id=profile.id,
                user_id=profile.user_id,
                user_type=profile.user_type or "college_student",
                status="completed",
                questions_answered=8,
                min_questions=8,
                max_questions=15,
                confidence=0.82,
                current_traits=trait_scores,
                current_state={"marker": PRESENTATION_DEMO_MARKER},
                started_at=now - timedelta(minutes=18),
                completed_at=now - timedelta(minutes=2),
            )
            self.db.add(session)
            self.db.flush()
        result_exists = self.db.scalar(
            select(PsychometricResult.id).where(PsychometricResult.session_id == session_id)
        )
        if result_exists is None:
            self.db.add(
                PsychometricResult(
                    session_id=session_id,
                    student_profile_id=profile.id,
                    user_id=profile.user_id,
                    trait_scores=trait_scores,
                    confidence=0.82,
                    question_count=8,
                    scoring_config_hash=PRESENTATION_DEMO_MARKER,
                )
            )

    def _ensure_demo_admin_items(
        self,
        *,
        created_by_user_id: int | None,
    ) -> None:
        items = [
            {
                "item_type": "program",
                "slug": "presentation-demo-ai-foundation-bridge",
                "title": "AI Foundation Bridge",
                "summary": (
                    "Bridge option for students who show AI interest but need "
                    "stronger mathematics and programming proof."
                ),
                "payload": {
                    "school_id": "school-engineering",
                    "school_name": "School of Engineering",
                    "degree_level": "undergraduate",
                    "duration_years": 4,
                    "branches": ["Computer Science", "AI"],
                    "priority_skills": ["Python", "Mathematics", "Data Handling"],
                    "career_paths": ["AI Product Engineer", "Data Analyst"],
                    "admission_fit_signals": [
                        "Computer science subject interest",
                        "Logical reasoning confidence",
                    ],
                    "reality_checks": [
                        "AI outcomes need coding, mathematics, and project evidence."
                    ],
                    "marker": PRESENTATION_DEMO_MARKER,
                },
            },
            {
                "item_type": "training_program",
                "slug": "presentation-demo-aptitude-sprint",
                "title": "Aptitude and Interview Sprint",
                "summary": "Four-week placement preparation plan for final-year students.",
                "payload": {
                    "skills": ["Aptitude", "DSA", "communication"],
                    "duration": "4 weeks",
                    "outcome": "Placement interview readiness",
                    "marker": PRESENTATION_DEMO_MARKER,
                },
            },
            {
                "item_type": "internship_opportunity",
                "slug": "presentation-demo-internship-lab",
                "title": "Backend API Internship Lab",
                "summary": "Guided project internship for API, SQL, and deployment proof.",
                "payload": {
                    "company": "Campus Innovation Lab",
                    "location": "Hybrid",
                    "duration": "6 weeks",
                    "skills": ["FastAPI", "SQL", "Git"],
                    "eligibility": ["B.Tech CSE", "2+ projects preferred"],
                    "apply_url": "https://example.com/demo/internship",
                    "deadline": "Rolling",
                    "marker": PRESENTATION_DEMO_MARKER,
                },
            },
            {
                "item_type": "placement_company",
                "slug": "presentation-demo-placement-company",
                "title": PRESENTATION_DEMO_COMPANY_NAME,
                "summary": "Product engineering employer for campus readiness demos.",
                "payload": {
                    "industry": "Software Products",
                    "location": "Bengaluru / Remote",
                    "marker": PRESENTATION_DEMO_MARKER,
                },
            },
            {
                "item_type": "institution_policy",
                "slug": "presentation-demo-counseling-policy",
                "title": "Counseling Evidence Policy",
                "summary": (
                    "Counselors should connect every recommendation to profile, quiz, "
                    "resume, or approved knowledge evidence."
                ),
                "payload": {"marker": PRESENTATION_DEMO_MARKER},
            },
            {
                "item_type": "knowledge_template",
                "slug": "presentation-demo-knowledge-template",
                "title": "Branch Counseling Evidence Template",
                "summary": "Template for uploading approved branch and placement guidance.",
                "payload": {
                    "source_type": "counseling",
                    "tags": ["branch guidance", "placement readiness"],
                    "marker": PRESENTATION_DEMO_MARKER,
                },
            },
            {
                "item_type": "institution_content",
                "slug": "presentation-demo-homepage-notice",
                "title": "Placement Readiness Week Notice",
                "summary": "Register for resume review, aptitude practice, and mock interviews.",
                "payload": {
                    "audience": "college_student",
                    "action_url": "/training",
                    "marker": PRESENTATION_DEMO_MARKER,
                },
            },
        ]
        for item in items:
            row = self.db.scalar(
                select(AdminManagedItem).where(
                    AdminManagedItem.item_type == item["item_type"],
                    AdminManagedItem.slug == item["slug"],
                )
            )
            if row is not None:
                continue
            self.db.add(
                AdminManagedItem(
                    item_type=item["item_type"],
                    slug=item["slug"],
                    title=item["title"],
                    summary=item["summary"],
                    status="active",
                    payload=item["payload"],
                    created_by_user_id=created_by_user_id,
                    updated_by_user_id=created_by_user_id,
                )
            )

    def _ensure_demo_company(
        self,
        *,
        created_by_user_id: int | None,
    ) -> PlacementCompany:
        row = self.db.scalar(
            select(PlacementCompany).where(
                PlacementCompany.name == PRESENTATION_DEMO_COMPANY_NAME
            )
        )
        if row is not None:
            return row
        row = PlacementCompany(
            name=PRESENTATION_DEMO_COMPANY_NAME,
            status="active",
            website="https://example.com/demo/technova",
            industry="Software Products",
            location="Bengaluru / Remote",
            contact_name="Campus Hiring Team",
            contact_email="campus.hiring@example.com",
            notes=f"Seeded for presentation demo: {PRESENTATION_DEMO_MARKER}",
            created_by_user_id=created_by_user_id,
            updated_by_user_id=created_by_user_id,
        )
        self.db.add(row)
        self.db.flush()
        return row

    def _ensure_demo_opportunity(
        self,
        *,
        company: PlacementCompany,
        created_by_user_id: int | None,
    ) -> None:
        row = self.db.scalar(
            select(PlacementOpportunity).where(
                PlacementOpportunity.title == PRESENTATION_DEMO_OPPORTUNITY_TITLE,
                PlacementOpportunity.company == PRESENTATION_DEMO_COMPANY_NAME,
            )
        )
        if row is not None:
            return
        self.db.add(
            PlacementOpportunity(
                title=PRESENTATION_DEMO_OPPORTUNITY_TITLE,
                company=PRESENTATION_DEMO_COMPANY_NAME,
                company_id=company.id,
                opportunity_type="placement",
                status="active",
                description=(
                    "Campus hiring role for students with API project evidence, SQL "
                    "comfort, and interview readiness."
                ),
                location="Bengaluru / Remote",
                work_mode="hybrid",
                deadline_at=datetime.now(timezone.utc) + timedelta(days=21),
                eligibility={
                    "degrees": ["B.Tech"],
                    "specializations": ["CSE", "IT", "AIML"],
                    "min_cgpa": 7.0,
                    "marker": PRESENTATION_DEMO_MARKER,
                },
                required_skills=["Python", "SQL", "APIs", "Git"],
                apply_url="https://example.com/demo/technova-campus-sprint",
                package_label="4.5-6 LPA",
                vacancies=12,
                contact_name="Campus Hiring Team",
                contact_email="campus.hiring@example.com",
                hiring_stages=["Resume screen", "Aptitude", "Technical interview"],
                created_by_user_id=created_by_user_id,
                updated_by_user_id=created_by_user_id,
            )
        )

    def _ensure_demo_notifications(
        self,
        *,
        twelfth_profile: StudentProfile,
        college_profile: StudentProfile,
        created_by_user_id: int | None,
    ) -> None:
        notifications = [
            (
                twelfth_profile,
                "Review branch guidance plan",
                (
                    "Your AI foundation path is ready. Review the weekly practice "
                    "plan before the counselor discussion."
                ),
                "/dashboard",
            ),
            (
                college_profile,
                "Placement sprint is open",
                (
                    "Complete resume polish and register for the aptitude sprint "
                    "before applying to the campus role."
                ),
                "/training",
            ),
        ]
        for profile, title, message, action_url in notifications:
            exists = self.db.scalar(
                select(UserNotification.id).where(
                    UserNotification.recipient_user_id == profile.user_id,
                    UserNotification.title == title,
                    cast(UserNotification.event_metadata, String).like(
                        f"%{PRESENTATION_DEMO_MARKER}%"
                    ),
                )
            )
            if exists is not None:
                continue
            self.db.add(
                UserNotification(
                    recipient_user_id=profile.user_id,
                    profile_id=profile.id,
                    notification_type="presentation_demo",
                    title=title,
                    message=message,
                    action_url=action_url,
                    priority="high",
                    created_by_user_id=created_by_user_id,
                    event_metadata={"marker": PRESENTATION_DEMO_MARKER},
                )
            )

    def _has_profile_record(self, model, profile_id: int) -> bool:
        return bool(
            self.db.scalar(
                select(model.id).where(model.student_profile_id == profile_id).limit(1)
            )
        )

    def _eligible_user_filter(self):
        email = func.lower(User.email)
        return or_(*(email.like(pattern) for pattern in _SAFE_EMAIL_PATTERNS))

    def _eligible_user_ids(self) -> list[int]:
        return list(
            self.db.scalars(
                select(User.id).where(self._eligible_user_filter()).order_by(User.id)
            )
        )

    def _profile_ids(self, user_ids: list[int]) -> list[int]:
        if not user_ids:
            return []
        return list(
            self.db.scalars(
                select(StudentProfile.id)
                .where(StudentProfile.user_id.in_(user_ids))
                .order_by(StudentProfile.id)
            )
        )

    def _quiz_session_ids(
        self,
        *,
        user_ids: list[int],
        profile_ids: list[int],
    ) -> list[str]:
        predicates = []
        if user_ids:
            predicates.append(PsychometricSession.user_id.in_(user_ids))
        if profile_ids:
            predicates.append(PsychometricSession.student_profile_id.in_(profile_ids))
        if not predicates:
            return []
        return list(
            self.db.scalars(
                select(PsychometricSession.id)
                .where(or_(*predicates))
                .order_by(PsychometricSession.id)
            )
        )

    def _eligible_rag_filter(self):
        title = func.lower(RAGDocumentSource.title)
        tags = func.lower(cast(RAGDocumentSource.tags, String))
        programs = func.lower(cast(RAGDocumentSource.program_ids, String))
        return or_(
            *(title.like(pattern) for pattern in _SAFE_SOURCE_TITLE_PATTERNS),
            *(tags.like(pattern) for pattern in _SAFE_SOURCE_TAG_PATTERNS),
            *(programs.like(pattern) for pattern in _SAFE_SOURCE_TAG_PATTERNS),
        )

    def _eligible_rag_source_ids(self) -> list[int]:
        return list(
            self.db.scalars(
                select(RAGDocumentSource.id)
                .where(self._eligible_rag_filter())
                .order_by(RAGDocumentSource.id)
            )
        )

    def _sample_emails(self) -> list[str]:
        return list(
            self.db.scalars(
                select(User.email)
                .where(self._eligible_user_filter())
                .order_by(User.email)
                .limit(5)
            )
        )

    def _sample_rag_titles(self) -> list[str]:
        return list(
            self.db.scalars(
                select(RAGDocumentSource.title)
                .where(self._eligible_rag_filter())
                .order_by(RAGDocumentSource.title)
                .limit(5)
            )
        )

    def _count_by_profile(self, model, profile_ids: list[int]) -> int:
        if not profile_ids:
            return 0
        return int(
            self.db.scalar(
                select(func.count(model.id)).where(
                    model.student_profile_id.in_(profile_ids)
                )
            )
            or 0
        )

    def _count_by_session(self, model, session_ids: list[str]) -> int:
        if not session_ids:
            return 0
        return int(
            self.db.scalar(
                select(func.count(model.id)).where(model.session_id.in_(session_ids))
            )
            or 0
        )

    def _count_analysis_jobs(
        self,
        user_ids: list[int],
        profile_ids: list[int],
    ) -> int:
        predicates = []
        if user_ids:
            predicates.append(AnalysisJob.user_id.in_(user_ids))
        if profile_ids:
            predicates.append(AnalysisJob.student_profile_id.in_(profile_ids))
        if not predicates:
            return 0
        return int(
            self.db.scalar(select(func.count(AnalysisJob.id)).where(or_(*predicates)))
            or 0
        )

    def _count_quiz_results(
        self,
        *,
        user_ids: list[int],
        profile_ids: list[int],
        session_ids: list[str],
    ) -> int:
        predicates = []
        if user_ids:
            predicates.append(PsychometricResult.user_id.in_(user_ids))
        if profile_ids:
            predicates.append(PsychometricResult.student_profile_id.in_(profile_ids))
        if session_ids:
            predicates.append(PsychometricResult.session_id.in_(session_ids))
        if not predicates:
            return 0
        return int(
            self.db.scalar(
                select(func.count(PsychometricResult.id)).where(or_(*predicates))
            )
            or 0
        )

    def _count_rag_chunks(self, source_ids: list[int]) -> int:
        if not source_ids:
            return 0
        return int(
            self.db.scalar(
                select(func.count(RAGDocumentChunk.id)).where(
                    RAGDocumentChunk.source_id.in_(source_ids)
                )
            )
            or 0
        )

    def _delete_by_profile(self, model, profile_ids: list[int]) -> None:
        if not profile_ids:
            return
        self.db.execute(delete(model).where(model.student_profile_id.in_(profile_ids)))
