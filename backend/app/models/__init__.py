# Import models here so SQLAlchemy metadata is populated when needed.
from app.models.admin_management import AdminManagedItem  # noqa: F401
from app.models.analysis_job import AnalysisJob  # noqa: F401
from app.models.career_analysis import CareerAnalysis  # noqa: F401
from app.models.company_fit import CompanyFit  # noqa: F401
from app.models.employability_score import EmployabilityScore  # noqa: F401
from app.models.institution_override import InstitutionOverride  # noqa: F401
from app.models.internship_readiness import InternshipReadiness  # noqa: F401
from app.models.notification import UserNotification  # noqa: F401
from app.models.placement_opportunity import (  # noqa: F401
    PlacementActivityEvent,
    PlacementApplication,
    PlacementCompany,
    PlacementInterviewRound,
    PlacementOpportunity,
)
from app.models.placement_risk import PlacementRisk  # noqa: F401
from app.models.psychometric_answer import PsychometricAnswer  # noqa: F401
from app.models.psychometric_question import PsychometricQuestion  # noqa: F401
from app.models.psychometric_result import PsychometricResult  # noqa: F401
from app.models.psychometric_session import PsychometricSession  # noqa: F401
from app.models.rag_document import RAGDocumentChunk, RAGDocumentSource  # noqa: F401
from app.models.resume_analysis import ResumeAnalysis  # noqa: F401
from app.models.role_gap_analysis import RoleGapAnalysis  # noqa: F401
from app.models.student_profile import StudentProfile  # noqa: F401
from app.models.user import User  # noqa: F401
