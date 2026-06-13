from __future__ import annotations

import hashlib
import json
import logging
from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import Select, select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.scoring import PSYCHOMETRIC_SCORING
from app.models.psychometric_answer import PsychometricAnswer
from app.models.psychometric_question import PsychometricQuestion
from app.models.psychometric_result import PsychometricResult
from app.models.psychometric_session import PsychometricSession
from app.models.student_profile import StudentProfile
from app.schemas.psychometric_quiz import PsychometricAnswerSubmit
from app.services.llm_cost_control import record_llm_event
from app.services.psychometric_question_service import PsychometricQuestionService
from app.services.psychometric_trait_service import PsychometricTraitService


logger = logging.getLogger(__name__)


def _scoring_config_hash() -> str:
    payload = {
        "trait_version": PSYCHOMETRIC_SCORING.trait_version,
        "min_questions": PSYCHOMETRIC_SCORING.min_questions,
        "max_questions": PSYCHOMETRIC_SCORING.max_questions,
        "confidence_threshold": PSYCHOMETRIC_SCORING.confidence_threshold,
        "max_tokens_per_session": PSYCHOMETRIC_SCORING.max_tokens_per_session,
        "traits": PSYCHOMETRIC_SCORING.traits or {},
    }
    encoded = json.dumps(payload, sort_keys=True).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


class PsychometricSessionService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.settings = get_settings()
        self.question_service = PsychometricQuestionService(db)
        self.trait_service = PsychometricTraitService()

    def _session_stmt(self, session_id: str) -> Select[tuple[PsychometricSession]]:
        return select(PsychometricSession).where(PsychometricSession.id == session_id)

    def get_session(
        self,
        session_id: str,
        user_id: int,
        *,
        allow_admin: bool = False,
    ) -> PsychometricSession | None:
        session = self.db.scalar(self._session_stmt(session_id))
        if session is None:
            return None
        if not allow_admin and session.user_id != user_id:
            return None
        return session

    def get_result(
        self,
        session_id: str,
        user_id: int,
        *,
        allow_admin: bool = False,
    ) -> PsychometricResult | None:
        session = self.get_session(session_id, user_id, allow_admin=allow_admin)
        if session is None:
            return None
        return self.db.scalar(
            select(PsychometricResult).where(PsychometricResult.session_id == session_id)
        )

    def get_current_question(self, session: PsychometricSession) -> PsychometricQuestion | None:
        if not session.current_question_id:
            return None
        return self.db.get(PsychometricQuestion, session.current_question_id)

    def _get_active_session(self, profile_id: int, user_id: int) -> PsychometricSession | None:
        stmt = (
            select(PsychometricSession)
            .where(
                PsychometricSession.student_profile_id == profile_id,
                PsychometricSession.user_id == user_id,
                PsychometricSession.status.in_(["queued", "in_progress"]),
            )
            .order_by(PsychometricSession.created_at.desc())
        )
        return self.db.scalar(stmt)

    def start_session(
        self,
        profile_id: int,
        user_id: int,
        *,
        allow_admin: bool = False,
    ) -> PsychometricSession:
        profile = self.db.get(StudentProfile, profile_id)
        if profile is None or (profile.user_id != user_id and not allow_admin):
            raise ValueError("Profile not found")

        effective_user_id = user_id
        if allow_admin:
            effective_user_id = profile.user_id

        active = self._get_active_session(profile_id, effective_user_id)
        if active is not None:
            if active.current_question_id is None:
                self.question_service.generate_next_question(active)
            return active

        session = PsychometricSession(
            id=str(uuid4()),
            student_profile_id=profile_id,
            user_id=effective_user_id,
            user_type=profile.user_type or "college_student",
            status="queued",
            min_questions=self.settings.psychometric_min_questions,
            max_questions=self.settings.psychometric_max_questions,
            current_traits=self.trait_service.initial_traits(),
            current_state={"recent_answers": [], "fallback_count": 0, "delta_history": []},
            schema_version=self.settings.psychometric_schema_version,
            prompt_version=self.settings.psychometric_prompt_version,
        )
        self.db.add(session)
        self.db.commit()
        self.db.refresh(session)

        self.question_service.generate_next_question(session)
        self.db.refresh(session)
        return session

    def submit_answer(
        self,
        session_id: str,
        payload: PsychometricAnswerSubmit,
        user_id: int,
        *,
        allow_admin: bool = False,
    ) -> tuple[PsychometricSession, bool]:
        session = self.get_session(session_id, user_id, allow_admin=allow_admin)
        if session is None:
            raise ValueError("Session not found")

        if session.status not in {"queued", "in_progress"}:
            return session, True

        question = self.db.get(PsychometricQuestion, payload.question_id)
        if question is None or question.session_id != session.id:
            raise ValueError("Question not found")

        if session.current_question_id and payload.question_id != session.current_question_id:
            raise ValueError("Only the current question can be answered")

        duplicate_by_question = self.db.scalar(
            select(PsychometricAnswer).where(
                PsychometricAnswer.session_id == session.id,
                PsychometricAnswer.question_id == question.id,
            )
        )
        if duplicate_by_question is not None:
            return session, True

        if payload.idempotency_key:
            duplicate_by_key = self.db.scalar(
                select(PsychometricAnswer).where(
                    PsychometricAnswer.session_id == session.id,
                    PsychometricAnswer.idempotency_key == payload.idempotency_key,
                )
            )
            if duplicate_by_key is not None:
                return session, True

        selected_option = None
        for option in question.options:
            if option.get("option_id") == payload.option_id:
                selected_option = option
                break
        if selected_option is None:
            raise ValueError("Invalid option_id")

        answer = PsychometricAnswer(
            id=payload.answer_id,
            session_id=session.id,
            question_id=question.id,
            idempotency_key=payload.idempotency_key,
            selected_option_id=payload.option_id,
            selected_option_text=selected_option.get("text"),
            trait_effect=selected_option.get("trait_effect", {}),
            response_ms=payload.response_ms,
        )
        self.db.add(answer)

        questions_answered = session.questions_answered + 1
        current_state = dict(session.current_state or {})

        traits, confidence, state_update = self.trait_service.apply_trait_effect(
            current_traits=session.current_traits,
            trait_effect=selected_option.get("trait_effect", {}),
            questions_answered=questions_answered,
            min_questions=session.min_questions,
            previous_state=current_state,
        )

        recent_answers = current_state.get("recent_answers", [])
        if not isinstance(recent_answers, list):
            recent_answers = []
        recent_answers.append(
            {
                "question_id": question.id,
                "option_id": payload.option_id,
                "trait_tag": question.trait_tag,
            }
        )
        recent_answers = recent_answers[-3:]

        fallback_count = int(current_state.get("fallback_count", 0))
        if question.source in {"fallback", "guided"}:
            fallback_count += 1

        current_state.update(state_update)
        current_state["recent_answers"] = recent_answers
        current_state["fallback_count"] = fallback_count

        session.current_traits = traits
        session.current_state = current_state
        session.confidence = confidence
        session.questions_answered = questions_answered
        session.updated_at = datetime.now(timezone.utc)

        reached_budget = session.tokens_used >= self.settings.psychometric_max_tokens_per_session
        can_complete_by_confidence = (
            questions_answered >= session.min_questions
            and confidence >= self.settings.psychometric_confidence_threshold
        )
        should_complete = reached_budget or questions_answered >= session.max_questions or can_complete_by_confidence

        if should_complete:
            session.status = "completed"
            session.current_question_id = None
            session.completed_at = datetime.now(timezone.utc)
            duration_ms: int | None = None
            if session.started_at is not None:
                duration_ms = max(
                    0,
                    int((session.completed_at - session.started_at).total_seconds() * 1000),
                )
            result = PsychometricResult(
                session_id=session.id,
                student_profile_id=session.student_profile_id,
                user_id=session.user_id,
                trait_scores=session.current_traits,
                confidence=session.confidence,
                question_count=session.questions_answered,
                fallback_count=fallback_count,
                trait_version=PSYCHOMETRIC_SCORING.trait_version,
                schema_version=session.schema_version,
                prompt_version=session.prompt_version,
                scoring_config_hash=_scoring_config_hash(),
                completed_at=session.completed_at,
            )
            self.db.add(result)
            self.db.commit()
            self.db.refresh(session)
            event_count = record_llm_event(
                user_key=f"user:{session.user_id}",
                endpoint="quiz_session",
                event="quiz_completed",
            )
            logger.info(
                "quiz_completed session_id=%s user_id=%s profile_id=%s questions=%s confidence=%s fallback_count=%s duration_ms=%s llm_failure_count=%s event_count=%s",
                session.id,
                session.user_id,
                session.student_profile_id,
                session.questions_answered,
                round(session.confidence, 4),
                fallback_count,
                duration_ms,
                session.llm_failure_count,
                event_count,
            )
            return session, False

        self.db.commit()
        self.db.refresh(session)
        self.question_service.generate_next_question(session)
        self.db.refresh(session)
        return session, False

    def record_abandonment(
        self,
        session_id: str,
        user_id: int,
        *,
        reason: str | None = None,
        allow_admin: bool = False,
    ) -> PsychometricSession:
        session = self.get_session(session_id, user_id, allow_admin=allow_admin)
        if session is None:
            raise ValueError("Session not found")

        if session.status not in {"queued", "in_progress"}:
            return session

        now = datetime.now(timezone.utc)
        current_state = dict(session.current_state or {})

        abandon_events = current_state.get("abandon_events", [])
        if not isinstance(abandon_events, list):
            abandon_events = []

        event = {"at": now.isoformat()}
        if reason:
            event["reason"] = reason
        abandon_events.append(event)

        current_state["abandon_events"] = abandon_events[-10:]
        current_state["abandon_count"] = int(current_state.get("abandon_count", 0)) + 1
        current_state["last_abandoned_at"] = now.isoformat()
        if reason:
            current_state["last_abandon_reason"] = reason
        state_abandon_count = int(current_state["abandon_count"])

        session.current_state = current_state
        session.updated_at = now

        self.db.commit()
        self.db.refresh(session)
        event_count = record_llm_event(
            user_key=f"user:{session.user_id}",
            endpoint="quiz_session",
            event="quiz_abandoned",
        )
        logger.info(
            "quiz_abandoned session_id=%s user_id=%s profile_id=%s status=%s reason=%s abandon_count=%s llm_failure_count=%s event_count=%s",
            session.id,
            session.user_id,
            session.student_profile_id,
            session.status,
            reason or "unspecified",
            state_abandon_count,
            session.llm_failure_count,
            event_count,
        )
        return session
