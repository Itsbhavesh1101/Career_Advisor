from __future__ import annotations

import logging
import time
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeoutError
from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.psychometric_question import PsychometricQuestion
from app.models.psychometric_session import PsychometricSession
from app.schemas.psychometric_quiz import PsychometricQuestionLLMOutput
from app.services.llm_client import LLMClient
from app.services.llm_cost_control import get_llm_usage, record_llm_event
from app.services.psychometric_fallback_bank import select_fallback_question


logger = logging.getLogger(__name__)


def _apply_question_metadata(
    session: PsychometricSession,
    payload: dict,
    *,
    ai_status: str,
) -> None:
    current_state = dict(session.current_state or {})
    current_state["ai_status"] = payload.get("ai_status") or ai_status
    current_state["adaptation_reason"] = payload.get("adaptation_reason")
    current_state["next_focus"] = payload.get("next_focus") or payload.get("trait_tag")
    session.current_state = current_state


class PsychometricQuestionService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.settings = get_settings()
        self.llm_client = LLMClient()

    def get_question(self, question_id: str) -> PsychometricQuestion | None:
        return self.db.get(PsychometricQuestion, question_id)

    def list_session_questions(self, session_id: str) -> list[PsychometricQuestion]:
        stmt = (
            select(PsychometricQuestion)
            .where(PsychometricQuestion.session_id == session_id)
            .order_by(PsychometricQuestion.position.asc())
        )
        return list(self.db.scalars(stmt).all())

    def _find_session_question_by_position(
        self,
        *,
        session_id: str,
        position: int,
    ) -> PsychometricQuestion | None:
        return self.db.scalar(
            select(PsychometricQuestion).where(
                PsychometricQuestion.session_id == session_id,
                PsychometricQuestion.position == position,
            )
        )

    def _generate_with_soft_deadline(
        self,
        *,
        user_key: str,
        session_id: str,
        user_type: str,
        traits: dict[str, float],
        answers_summary: list[dict],
        schema_version: str,
        prompt_version: str,
    ) -> dict:
        executor = ThreadPoolExecutor(max_workers=1)
        future = executor.submit(
            self.llm_client.generate_psychometric_question,
            user_key=user_key,
            session_id=session_id,
            user_type=user_type,
            traits=traits,
            answers_summary=answers_summary,
            schema_version=schema_version,
            prompt_version=prompt_version,
        )
        try:
            return future.result(timeout=float(self.settings.psychometric_soft_timeout_seconds))
        finally:
            executor.shutdown(wait=False, cancel_futures=True)

    def generate_next_question(self, session: PsychometricSession) -> PsychometricQuestion:
        if session.question_generation_lock and session.current_question_id:
            existing = self.db.get(PsychometricQuestion, session.current_question_id)
            if existing is not None:
                return existing

        session.question_generation_lock = True
        try:
            self.db.commit()
        except Exception:
            self.db.rollback()
            raise

        try:
            questions = self.list_session_questions(session.id)
            asked_traits = {q.trait_tag for q in questions if q.trait_tag}
            position = session.current_question_index + 1
            existing_for_position = self._find_session_question_by_position(
                session_id=session.id,
                position=position,
            )
            if existing_for_position is not None:
                session.current_question_id = existing_for_position.id
                session.current_question_index = max(
                    session.current_question_index,
                    existing_for_position.position,
                )
                session.status = "in_progress"
                session.updated_at = datetime.now(timezone.utc)
                self.db.commit()
                self.db.refresh(session)
                return existing_for_position

            generation_started = time.perf_counter()
            user_key = f"user:{session.user_id}"

            source = "llm"
            prompt_version = self.settings.psychometric_prompt_version
            schema_version = self.settings.psychometric_schema_version

            if session.breaker_open or session.fallback_mode:
                payload = select_fallback_question(
                    user_type=session.user_type,
                    asked_trait_tags=asked_traits,
                    position=position,
                    current_traits=session.current_traits,
                    recent_answers=(session.current_state or {}).get("recent_answers", []),
                )
                source = "guided"
                _apply_question_metadata(session, payload, ai_status="guided_adaptive")
                latency_ms = int((time.perf_counter() - generation_started) * 1000)
                event_count = record_llm_event(
                    user_key=user_key,
                    endpoint="quiz_session",
                    event="quiz_fallback_triggered",
                )
                logger.info(
                    "quiz_fallback_triggered session_id=%s user_id=%s reason=%s latency_ms=%s llm_failure_count=%s event_count=%s",
                    session.id,
                    session.user_id,
                    "breaker_mode",
                    latency_ms,
                    session.llm_failure_count,
                    event_count,
                )
            else:
                usage_scope = f"quiz_session:{session.id}"
                usage_before = int(
                    get_llm_usage(user_key, "quiz_generation", usage_scope=usage_scope).get(
                        "tokens", 0
                    )
                )
                try:
                    llm_payload = self._generate_with_soft_deadline(
                        user_key=user_key,
                        session_id=session.id,
                        user_type=session.user_type,
                        traits=session.current_traits,
                        answers_summary=(session.current_state or {}).get("recent_answers", []),
                        schema_version=schema_version,
                        prompt_version=prompt_version,
                    )
                    parsed = PsychometricQuestionLLMOutput.model_validate(llm_payload)
                    payload = {
                        "question": parsed.question,
                        "trait_tag": parsed.trait_tag,
                        "options": [option.model_dump() for option in parsed.options],
                    }
                    session.llm_failure_count = 0
                    _apply_question_metadata(
                        session,
                        {
                            "ai_status": "ai_generated",
                            "adaptation_reason": (
                                f"AI selected {parsed.trait_tag.replace('_', ' ')} "
                                "from your recent answers."
                            ),
                            "next_focus": parsed.trait_tag.replace("_", " ").title(),
                        },
                        ai_status="ai_generated",
                    )

                    usage_after = int(
                        get_llm_usage(user_key, "quiz_generation", usage_scope=usage_scope).get(
                            "tokens", 0
                        )
                    )
                    consumed = max(0, usage_after - usage_before)
                    session.tokens_used += consumed
                    latency_ms = int((time.perf_counter() - generation_started) * 1000)
                    event_count = record_llm_event(
                        user_key=user_key,
                        endpoint="quiz_session",
                        event="quiz_question_generated",
                    )

                    logger.info(
                        "quiz_question_generated session_id=%s user_id=%s source=%s tokens_used=%s latency_ms=%s llm_failure_count=%s event_count=%s",
                        session.id,
                        session.user_id,
                        source,
                        session.tokens_used,
                        latency_ms,
                        session.llm_failure_count,
                        event_count,
                    )
                except FutureTimeoutError:
                    source = "guided"
                    payload = select_fallback_question(
                        user_type=session.user_type,
                        asked_trait_tags=asked_traits,
                        position=position,
                        current_traits=session.current_traits,
                        recent_answers=(session.current_state or {}).get("recent_answers", []),
                    )
                    _apply_question_metadata(session, payload, ai_status="guided_adaptive")
                    record_llm_event(user_key=user_key, endpoint="quiz_generation", event="soft_timeout")
                    latency_ms = int((time.perf_counter() - generation_started) * 1000)
                    event_count = record_llm_event(
                        user_key=user_key,
                        endpoint="quiz_session",
                        event="quiz_fallback_triggered",
                    )
                    logger.info(
                        "quiz_fallback_triggered session_id=%s user_id=%s reason=%s latency_ms=%s llm_failure_count=%s event_count=%s",
                        session.id,
                        session.user_id,
                        "soft_timeout",
                        latency_ms,
                        session.llm_failure_count,
                        event_count,
                    )
                except Exception:
                    session.llm_failure_count += 1
                    source = "guided"
                    payload = select_fallback_question(
                        user_type=session.user_type,
                        asked_trait_tags=asked_traits,
                        position=position,
                        current_traits=session.current_traits,
                        recent_answers=(session.current_state or {}).get("recent_answers", []),
                    )
                    _apply_question_metadata(session, payload, ai_status="recovering")
                    record_llm_event(user_key=user_key, endpoint="quiz_generation", event="generation_error")
                    latency_ms = int((time.perf_counter() - generation_started) * 1000)
                    event_count = record_llm_event(
                        user_key=user_key,
                        endpoint="quiz_session",
                        event="quiz_fallback_triggered",
                    )
                    logger.info(
                        "quiz_fallback_triggered session_id=%s user_id=%s reason=%s latency_ms=%s llm_failure_count=%s event_count=%s",
                        session.id,
                        session.user_id,
                        "generation_error",
                        latency_ms,
                        session.llm_failure_count,
                        event_count,
                    )
                    if session.llm_failure_count >= self.settings.psychometric_breaker_threshold:
                        session.breaker_open = True
                        session.fallback_mode = False

            question = PsychometricQuestion(
                id=str(uuid4()),
                session_id=session.id,
                position=position,
                source=source,
                trait_tag=payload.get("trait_tag"),
                question_text=payload["question"],
                options=payload["options"],
                schema_version=schema_version,
                prompt_version=prompt_version,
            )
            self.db.add(question)

            session.current_question_id = question.id
            session.current_question_index = position
            session.status = "in_progress"
            if session.started_at is None:
                session.started_at = datetime.now(timezone.utc)
            session.updated_at = datetime.now(timezone.utc)

            try:
                self.db.commit()
            except IntegrityError as exc:
                self.db.rollback()
                recovered = self._find_session_question_by_position(
                    session_id=session.id,
                    position=position,
                )
                if recovered is None:
                    raise exc

                persisted_session = self.db.get(PsychometricSession, session.id)
                if persisted_session is not None:
                    persisted_session.current_question_id = recovered.id
                    persisted_session.current_question_index = max(
                        persisted_session.current_question_index,
                        recovered.position,
                    )
                    persisted_session.status = "in_progress"
                    persisted_session.updated_at = datetime.now(timezone.utc)
                    self.db.commit()
                    self.db.refresh(persisted_session)

                logger.info(
                    "quiz_question_recovered_duplicate session_id=%s position=%s",
                    session.id,
                    position,
                )
                return recovered

            self.db.refresh(question)
            self.db.refresh(session)
            return question
        except Exception:
            self.db.rollback()
            raise
        finally:
            try:
                if self.db.in_transaction():
                    self.db.rollback()
                persisted_session = self.db.get(PsychometricSession, session.id)
                if persisted_session is not None and persisted_session.question_generation_lock:
                    persisted_session.question_generation_lock = False
                    persisted_session.updated_at = datetime.now(timezone.utc)
                    self.db.commit()
            except Exception:
                self.db.rollback()
                logger.warning(
                    "quiz_question_lock_clear_failed session_id=%s",
                    session.id,
                    exc_info=True,
                )
