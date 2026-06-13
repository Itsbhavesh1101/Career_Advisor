from fastapi import APIRouter

from app.api.routes.admin_dashboard import router as admin_dashboard_router
from app.api.routes.admin_management import router as admin_management_router
from app.api.routes.admission_intelligence import router as admission_intelligence_router
from app.api.routes.auth import router as auth_router
from app.api.routes.branch_analysis import router as branch_analysis_router
from app.api.routes.chat import router as chat_router
from app.api.routes.company_fit import router as company_fit_router
from app.api.routes.employability import router as employability_router
from app.api.routes.jobs import router as jobs_router
from app.api.routes.internship_readiness import router as internship_readiness_router
from app.api.routes.industry_demand import router as industry_demand_router
from app.api.routes.institution import router as institution_router
from app.api.routes.notifications import router as notifications_router
from app.api.routes.placement_opportunities import router as placement_opportunities_router
from app.api.routes.placement_risk import router as placement_risk_router
from app.api.routes.placement_intelligence import router as placement_intelligence_router
from app.api.routes.psychometric_quiz import router as psychometric_quiz_router
from app.api.routes.rag import router as rag_router
from app.api.routes.role_gaps import router as role_gaps_router
from app.api.routes.resume import router as resume_router
from app.api.routes.training import router as training_router
from app.api.routes.career_analysis import router as career_analysis_router
from app.api.routes.health import router as health_router
from app.api.routes.student_profiles import router as student_profiles_router

api_router = APIRouter()
api_router.include_router(health_router)
api_router.include_router(auth_router, prefix="/api/v1")
api_router.include_router(admission_intelligence_router, prefix="/api/v1")
api_router.include_router(admin_dashboard_router, prefix="/api/v1")
api_router.include_router(admin_management_router, prefix="/api/v1")
api_router.include_router(branch_analysis_router, prefix="/api/v1")
api_router.include_router(chat_router, prefix="/api/v1")
api_router.include_router(company_fit_router, prefix="/api/v1")
api_router.include_router(employability_router, prefix="/api/v1")
api_router.include_router(jobs_router, prefix="/api/v1")
api_router.include_router(industry_demand_router, prefix="/api/v1")
api_router.include_router(institution_router, prefix="/api/v1")
api_router.include_router(internship_readiness_router, prefix="/api/v1")
api_router.include_router(notifications_router, prefix="/api/v1")
api_router.include_router(placement_opportunities_router, prefix="/api/v1")
api_router.include_router(placement_intelligence_router, prefix="/api/v1")
api_router.include_router(placement_risk_router, prefix="/api/v1")
api_router.include_router(psychometric_quiz_router, prefix="/api/v1")
api_router.include_router(rag_router, prefix="/api/v1")
api_router.include_router(role_gaps_router, prefix="/api/v1")
api_router.include_router(resume_router, prefix="/api/v1")
api_router.include_router(training_router, prefix="/api/v1")
api_router.include_router(student_profiles_router, prefix="/api/v1")
api_router.include_router(career_analysis_router, prefix="/api/v1")
