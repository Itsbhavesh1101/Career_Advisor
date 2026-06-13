from __future__ import annotations

import json

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.deps import get_current_user_context, get_db
from app.core.config import get_settings
from app.core.rate_limit import limiter
from app.models.student_profile import StudentProfile
from app.services.career_analysis_service import CareerAnalysisService
from app.services.llm_client import LLMClient

router = APIRouter(prefix="/chat", tags=["chat"])


class ChatRequest(BaseModel):
    message: str


class ChatResponse(BaseModel):
    response: str


@router.post("/{profile_id}", response_model=ChatResponse)
@limiter.limit(get_settings().chat_rate_limit)
def chat_with_advisor(
    request: Request,
    profile_id: int,
    payload: ChatRequest,
    db: Session = Depends(get_db),
    context=Depends(get_current_user_context),
) -> ChatResponse:
    del request
    current_user, role = context
    profile = db.get(StudentProfile, profile_id)
    if profile is None or (profile.user_id != current_user.id and role != "admin"):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Profile not found")

    analysis_service = CareerAnalysisService(db)
    analysis = analysis_service.get_analysis_by_profile_id(
        profile_id, current_user.id, allow_admin=role == "admin"
    )
    if analysis is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Analysis not found")

    is_twelfth = (profile.user_type or "college_student") == "twelfth_student"
    if is_twelfth:
        assistant_role = (
            "You are a practical admissions counselor for a 12th student. "
            "Help the student and parent understand branch fit, expectation-reality "
            "gaps, first-year effort, and the next counseling action."
        )
        answer_style = (
            "- Use counselor language, not generic career advice\n"
            "- Explain branch or program fit in plain terms\n"
            "- Correct unrealistic expectations respectfully\n"
            "- End with one clear next action for the student\n"
        )
    else:
        assistant_role = (
            "You are a placement readiness copilot for a college student. "
            "Help the student improve employability, resume evidence, projects, "
            "training focus, internship readiness, and placement actions."
        )
        answer_style = (
            "- Use action-oriented placement readiness language\n"
            "- Prioritize resume, project, role, and interview next steps\n"
            "- Be specific about skill gaps and proof to build\n"
            "- End with one clear next action for the student\n"
        )
    system_prompt = (
        f"{assistant_role}\n\n"
        "When answering:\n"
        "- Refer to the student's profile and existing analysis\n"
        "- Keep answers concise and structured\n"
        f"{answer_style}"
    )
    user_prompt = (
        "Student Profile:\n"
        f"Name: {profile.name}\n"
        f"Student Type: {profile.user_type or 'college_student'}\n"
        f"Degree: {profile.degree}\n"
        f"Specialization: {profile.specialization}\n"
        f"12th Percentage: {profile.twelfth_percentage}%\n"
        f"CGPA: {profile.cgpa}\n"
        f"Subjects: {', '.join(profile.subjects or [])}\n"
        f"Current Skills: {', '.join(profile.current_skills)}\n"
        f"Interests: {', '.join(profile.interests)}\n"
        f"Target Industry: {profile.target_industry}\n\n"
        "Program Fit Summary:\n"
        f"{json.dumps(analysis.program_fit_summary or {}, indent=2)}\n\n"
        "Program Recommendations:\n"
        f"{json.dumps(analysis.program_recommendations or [], indent=2)}\n\n"
        "Expectation Reality Checks:\n"
        f"{json.dumps(analysis.expectation_reality_checks or [], indent=2)}\n\n"
        "Career Recommendations:\n"
        f"{json.dumps(analysis.career_recommendations, indent=2)}\n\n"
        "Skill Gaps:\n"
        f"{json.dumps(analysis.skill_gaps, indent=2)}\n\n"
        "Learning Roadmap:\n"
        f"{json.dumps(analysis.learning_roadmap, indent=2)}\n\n"
        "User Question:\n"
        f"{payload.message}\n"
    )

    llm = LLMClient()
    try:
        answer = llm.generate_chat_response(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            temperature=0.6,
            max_output_tokens=900,
            user_id=current_user.id,
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"LLM chat generation failed: {exc}",
        ) from exc

    return ChatResponse(response=answer)
