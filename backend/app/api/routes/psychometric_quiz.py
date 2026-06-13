from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user_context, get_db
from app.core.config import get_settings
from app.core.rate_limit import limiter
from app.models.psychometric_question import PsychometricQuestion
from app.models.psychometric_session import PsychometricSession
from app.schemas.psychometric_quiz import (
    PsychometricAbandonSubmit,
    PsychometricAnswerRead,
    PsychometricAnswerSubmit,
    PsychometricQuestionOption,
    PsychometricQuestionRead,
    PsychometricResultRead,
    PsychometricSessionStartRead,
    PsychometricSessionStatusRead,
)
from app.services.psychometric_session_service import PsychometricSessionService

router = APIRouter(prefix="/psychometric-quiz", tags=["psychometric-quiz"])


def _ensure_quiz_enabled() -> None:
    if not get_settings().psychometric_quiz_enabled:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Psychometric quiz is temporarily disabled",
        )


def _question_read(question: PsychometricQuestion | None) -> PsychometricQuestionRead | None:
    if question is None:
        return None
    return PsychometricQuestionRead(
        id=question.id,
        session_id=question.session_id,
        position=question.position,
        source=question.source,
        trait_tag=question.trait_tag,
        question_text=question.question_text,
        options=[PsychometricQuestionOption.model_validate(opt) for opt in question.options],
        schema_version=question.schema_version,
        prompt_version=question.prompt_version,
    )


def _session_read(
    session: PsychometricSession,
    question: PsychometricQuestion | None,
) -> PsychometricSessionStatusRead:
    current_state = session.current_state or {}
    return PsychometricSessionStatusRead(
        session_id=session.id,
        status=session.status,
        fallback_mode=session.fallback_mode,
        breaker_open=session.breaker_open,
        ai_status=str(current_state.get("ai_status") or "calibrating"),
        adaptation_reason=current_state.get("adaptation_reason"),
        next_focus=current_state.get("next_focus"),
        questions_answered=session.questions_answered,
        min_questions=session.min_questions,
        max_questions=session.max_questions,
        confidence=session.confidence,
        current_traits=session.current_traits,
        current_state=current_state,
        current_question=_question_read(question),
        created_at=session.created_at,
        updated_at=session.updated_at,
    )


@router.post("/start/{profile_id}", response_model=PsychometricSessionStartRead)
@limiter.limit(get_settings().quiz_start_rate_limit)
def start_quiz_session(
    request: Request,
    profile_id: int,
    db: Session = Depends(get_db),
    context=Depends(get_current_user_context),
) -> PsychometricSessionStartRead:
    del request
    _ensure_quiz_enabled()
    current_user, role = context
    service = PsychometricSessionService(db)
    try:
        session = service.start_session(profile_id, current_user.id, allow_admin=role == "admin")
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    question = service.get_current_question(session)
    return PsychometricSessionStartRead(session=_session_read(session, question))


@router.post("/{session_id}/answer", response_model=PsychometricAnswerRead)
@limiter.limit(get_settings().quiz_answer_rate_limit)
def submit_quiz_answer(
    request: Request,
    session_id: str,
    payload: PsychometricAnswerSubmit,
    db: Session = Depends(get_db),
    context=Depends(get_current_user_context),
) -> PsychometricAnswerRead:
    del request
    _ensure_quiz_enabled()
    current_user, role = context
    service = PsychometricSessionService(db)
    try:
        session, duplicate = service.submit_answer(
            session_id,
            payload,
            current_user.id,
            allow_admin=role == "admin",
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    question = service.get_current_question(session)
    return PsychometricAnswerRead(
        answer_id=payload.answer_id,
        accepted=not duplicate,
        duplicate=duplicate,
        session=_session_read(session, question),
    )


@router.get("/{session_id}/status", response_model=PsychometricSessionStatusRead)
@limiter.limit(get_settings().quiz_answer_rate_limit)
def get_quiz_status(
    request: Request,
    session_id: str,
    db: Session = Depends(get_db),
    context=Depends(get_current_user_context),
) -> PsychometricSessionStatusRead:
    del request
    _ensure_quiz_enabled()
    current_user, role = context
    service = PsychometricSessionService(db)
    session = service.get_session(session_id, current_user.id, allow_admin=role == "admin")
    if session is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")

    question = service.get_current_question(session)
    return _session_read(session, question)


@router.post("/{session_id}/abandon", response_model=PsychometricSessionStatusRead)
@limiter.limit(get_settings().quiz_answer_rate_limit)
def report_quiz_abandonment(
    request: Request,
    session_id: str,
    payload: PsychometricAbandonSubmit,
    db: Session = Depends(get_db),
    context=Depends(get_current_user_context),
) -> PsychometricSessionStatusRead:
    del request
    _ensure_quiz_enabled()
    current_user, role = context
    service = PsychometricSessionService(db)
    try:
        session = service.record_abandonment(
            session_id,
            current_user.id,
            reason=payload.reason,
            allow_admin=role == "admin",
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    question = service.get_current_question(session)
    return _session_read(session, question)


@router.get("/{session_id}/result", response_model=PsychometricResultRead)
def get_quiz_result(
    session_id: str,
    db: Session = Depends(get_db),
    context=Depends(get_current_user_context),
) -> PsychometricResultRead:
    _ensure_quiz_enabled()
    current_user, role = context
    service = PsychometricSessionService(db)
    result = service.get_result(session_id, current_user.id, allow_admin=role == "admin")
    if result is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Result not found")

    return PsychometricResultRead(
        session_id=result.session_id,
        student_profile_id=result.student_profile_id,
        user_id=result.user_id,
        trait_scores=result.trait_scores,
        confidence=result.confidence,
        question_count=result.question_count,
        fallback_count=result.fallback_count,
        trait_version=result.trait_version,
        schema_version=result.schema_version,
        prompt_version=result.prompt_version,
        scoring_config_hash=result.scoring_config_hash,
        completed_at=result.completed_at,
    )
